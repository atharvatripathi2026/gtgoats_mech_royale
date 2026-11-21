"""Run generated candidates in Docker with a trusted recipe and public inputs."""
from contextlib import ExitStack
from functools import lru_cache
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import secrets
import selectors
import statistics
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
CONTROLLER_FILES = (
    "adaptation.py", "bot.py", "loadout.py", "mechfight.py", "navigation.py",
    "policy.json", "recorder.py", "survival.py",
)
TEST_FILES = (
    "tests/test_bot.py", "tests/test_learning.py", "tests/test_squad16.py",
    "training/__init__.py", "training/arena.py", "training/squad16.py", "training/tune.py",
)
KIT_FILES = (
    "arena/v2/world.json", "arena/v2/terrain.i16", "check/check.py",
    "check/stream.jsonl.gz", "mechfight.schema.json",
)
PYTHON_IMAGE = (
    "python:3.13.18-slim-trixie@sha256:"
    "48d884813cf44e927cf64c5529dd630dd3b18338c6dc727991eef9b71e934a20"
)
OUTPUT_LIMIT = 256 * 1024
FILE_LIMIT = 4 * 1024 * 1024
DOCKER_SOCKET = Path("/var/run/docker.sock")


def _copy_files(source, target, names):
    """Copy only allowlisted regular files."""
    for name in names:
        path = source / name
        if any(p.is_symlink() for p in (path, *path.parents)):
            raise ValueError(f"Symlink rejected in check input: {name}")
        if not stat.S_ISREG(path.stat().st_mode):
            raise ValueError(f"Expected a regular check input: {name}")
        handle = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(handle, "rb") as stream:
            metadata = os.fstat(stream.fileno())
            if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > FILE_LIMIT:
                raise ValueError(f"Invalid check input size or type: {name}")
            data = stream.read(FILE_LIMIT + 1)
        if len(data) > FILE_LIMIT:
            raise ValueError(f"Check input exceeds size limit: {name}")
        dest = target / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
    for folder in (target, *(p for p in target.rglob("*") if p.is_dir())):
        folder.chmod(0o755)
    for path in target.rglob("*"):
        if path.is_file():
            path.chmod(0o444)


def _environment(home):
    # Never forward tokens, Docker contexts, credential helpers or Python hooks.
    return {"PATH": os.defpath + ":/usr/local/bin", "HOME": str(home), "LANG": "C.UTF-8"}


def _run(command, workdir, *, timeout, input_data=None):
    deadline = time.monotonic() + timeout
    output = bytearray()
    problem = None
    with subprocess.Popen(command, cwd=workdir, env=_environment(workdir),
                          stdin=subprocess.PIPE if input_data is not None else subprocess.DEVNULL,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          start_new_session=True) as child, selectors.DefaultSelector() as selector:
        selector.register(child.stdout, selectors.EVENT_READ)
        try:
            if input_data is not None:
                child.stdin.write(input_data)
                child.stdin.close()
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0 or not selector.select(remaining):
                    raise TimeoutError
                chunk = os.read(child.stdout.fileno(), 8192)
                if not chunk:
                    break
                output.extend(chunk)
                if len(output) > OUTPUT_LIMIT:
                    problem = "output_limit"
                    break
            if problem is None:
                child.wait(timeout=max(.001, deadline - time.monotonic()))
        except (TimeoutError, subprocess.TimeoutExpired):
            problem = "timeout"
        finally:
            if child.poll() is None:
                try:
                    os.killpg(child.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                child.wait()
    return child.returncode, output[:OUTPUT_LIMIT].decode(errors="replace"), problem


def _docker():
    if sys.platform != "linux":
        raise RuntimeError("Candidate checks require Linux or WSL2 with Docker Desktop integration")
    if not DOCKER_SOCKET.is_socket():
        raise RuntimeError(f"Enable the local Docker engine at {DOCKER_SOCKET} before running candidate checks")
    cli = shutil.which("docker", path=_environment("/tmp")["PATH"])
    if not cli:
        raise FileNotFoundError("Docker is required for candidate checks")
    return [cli, "--host", f"unix://{DOCKER_SOCKET}"]


@lru_cache(maxsize=1)
def _image():
    # stdin provides the entire trusted recipe. The build has no context.
    with tempfile.TemporaryDirectory(prefix="astra-claude-image-") as workdir:
        rc, log, problem = _run(
            [*_docker(), "build", "--quiet", "--network", "none", "-"], workdir,
            timeout=120, input_data=f"FROM {PYTHON_IMAGE}\n".encode(),
        )
    lines = log.strip().splitlines()
    if rc or problem or not lines or not re.fullmatch(r"sha256:[a-f0-9]{64}", lines[-1]):
        raise RuntimeError("Docker could not prepare the pinned Python check image")
    return lines[-1]


def _sandbox(name, controller, kit, image, *, unit=False, map_path=None):
    path = kit if unit else (map_path or kit / "arena")
    destination = "/kit" if unit else "/arena"
    cmd = [
        *_docker(), "run", "--rm", "--name", name, "-i", "--pull", "never",
        "--network", "none", "--user", "65534:65534", "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges", "--read-only", "--cpus", "1",
        "--memory", "512m", "--memory-swap", "512m", "--pids-limit", "128",
        "--log-driver", "none",
        "--tmpfs", "/tmp:rw,nosuid,nodev,noexec,mode=1777,size=64m",
        "--mount", f"type=bind,src={controller},dst=/bot,readonly",
        "--mount", f"type=bind,src={path},dst={destination},readonly",
        "--workdir", "/bot", "--entrypoint", "/usr/local/bin/python3",
        "--env", "PYTHONDONTWRITEBYTECODE=1", "--env", "PYTHONUNBUFFERED=1",
    ]
    if unit:
        cmd.extend(("--env", "MECHFIGHT_KIT=/kit"))
        return [*cmd, image, "-B", "-m", "unittest", "discover", "-s", "tests"]
    cmd.extend(("--attach", "stdin", "--attach", "stdout"))
    return [*cmd, image, "-B", "-u", "/bot/bot.py"]


def _check(command, name, workdir, output, label):
    try:
        code, log, problem = _run(command, workdir, timeout=120)
    finally:
        # A timed-out Docker client may leave a still-running container.
        _run([*_docker(), "rm", "-f", name], workdir, timeout=10)
    if output is not None:
        (output / f"{label}.log").write_text(log, encoding="utf-8")
    return {"ok": code == 0 and problem is None, "exit_code": code, "problem": problem}, log


def _invalid_number(_):
    raise ValueError("Local bot returned a non-finite JSON number")


def _finite_float(value):
    number = float(value)
    if not math.isfinite(number):
        _invalid_number(value)
    return number


class _WireBot:
    """The trusted engine receives actions over a narrow JSONL protocol."""
    def __init__(self, process, schema, limit, deadline):
        self.process = process
        self.schema = schema
        self.limit = limit
        self.deadline = deadline
        self.buffer = bytearray()
        for stream in (process.stdin, process.stdout):
            os.set_blocking(stream.fileno(), False)

    def _write(self, message, deadline):
        data = memoryview((json.dumps(message, allow_nan=False, separators=(",", ":")) + "\n").encode())
        fd = self.process.stdin.fileno()
        with selectors.DefaultSelector() as ready:
            ready.register(fd, selectors.EVENT_WRITE)
            while data:
                if time.monotonic() >= deadline or not ready.select(deadline - time.monotonic()):
                    raise TimeoutError("Local bot did not read its observation")
                try:
                    data = data[os.write(fd, data):]
                except BlockingIOError:
                    continue

    def _read(self, deadline, kind):
        fd = self.process.stdout.fileno()
        with selectors.DefaultSelector() as ready:
            ready.register(fd, selectors.EVENT_READ)
            while b"\n" not in self.buffer:
                if len(self.buffer) > self.limit:
                    raise ValueError("Local bot response exceeded protocol limit")
                if time.monotonic() >= deadline or not ready.select(deadline - time.monotonic()):
                    raise TimeoutError("Local bot did not answer")
                try:
                    chunk = os.read(fd, 8192)
                except BlockingIOError:
                    continue
                if not chunk:
                    raise ValueError("Local bot closed its response stream")
                self.buffer.extend(chunk)
        line, _, self.buffer = self.buffer.partition(b"\n")
        if len(line) > self.limit:
            raise ValueError("Local bot response exceeded protocol limit")
        message = json.loads(line, parse_constant=_invalid_number, parse_float=_finite_float)
        if not isinstance(message, dict) or self.schema.errors(message, kind):
            raise ValueError("Local bot response failed protocol validation")
        return message

    def start(self, hello):
        deadline = min(self.deadline, time.monotonic() + 25)
        self._write(hello, deadline)
        self._read(deadline, "Ready")

    def act(self, obs):
        deadline = min(self.deadline, time.monotonic() + 2)
        self._write(obs, deadline)
        message = self._read(deadline, "Action")
        if message["tick"] != obs["tick"]:
            raise ValueError("Local bot answered with the wrong tick")
        return message


def _paired_game(arena, seed, scenario, controller, kit, image, schema, workdir, deadline):
    if time.monotonic() >= deadline:
        raise TimeoutError("Paired checks reached their total time limit")
    deadline = min(deadline, time.monotonic() + 45)
    name = f"astra-claude-{uuid.uuid4().hex}"
    process = None
    def create(hello):
        nonlocal process
        # The host-owned arena supplies the map directory. No other host inputs
        # enter the candidate container.
        directory = Path(hello["map"]["dir"])
        command = _sandbox(name, controller, kit, image, map_path=directory)
        process = subprocess.Popen(command, cwd=workdir, env=_environment(workdir),
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.DEVNULL, start_new_session=True)
        bot = _WireBot(process, schema, hello["config"]["bot"]["max_line_bytes"], deadline)
        hello["map"]["dir"] = "/arena"
        bot.start(hello)
        return bot
    try:
        return arena.run(create, seed, scenario)
    finally:
        if process is not None:
            try:
                process.stdin.close()
                if process.poll() is None:
                    process.kill()
                process.wait(timeout=10)
            finally:
                process.stdout.close()
                _run([*_docker(), "rm", "-f", name], workdir, timeout=10)


def _paired(baseline, candidate, kit, workdir, image):
    from training.arena import Arena, SCENARIOS
    from training.squad16 import SquadArena

    base = workdir / "baseline"
    _copy_files(baseline, base, CONTROLLER_FILES)
    spec = importlib.util.spec_from_file_location("official_check", kit / "check" / "check.py")
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    schema = checker.Schema(str(kit / "mechfight.schema.json"))
    # Commit candidates cannot choose holdout seeds. Report seeds for replay.
    first_seed = secrets.randbelow(2**31 - 16)
    deadline = time.monotonic() + 240
    with ExitStack() as stack:
        generated = Arena(kit)
        stack.callback(generated.close)
        campus = Arena(kit, campus=True)
        stack.callback(campus.close)
        squad = SquadArena(kit)
        stack.callback(squad.close)
        four = [(arena, first_seed, scenario) for arena in (generated, campus) for scenario in SCENARIOS]
        squads = [(squad, first_seed + n, "squad16") for n in range(1, 5)]
        result = {"status": "completed", "seed_start": first_seed}
        for report, games in (("four_mech", four), ("squad16", squads)):
            scores = []
            for arena, seed, scenario in games:
                original = _paired_game(arena, seed, scenario, base, kit, image, schema, workdir, deadline)
                changed = _paired_game(arena, seed, scenario, candidate, kit, image, schema, workdir, deadline)
                scores.append(changed["score"] - original["score"])
            result[report] = {"pairs": len(scores), "mean_points_delta": statistics.mean(scores),
                              "improved": sum(d > 0 for d in scores), "tied": scores.count(0),
                              "regressed": sum(d < 0 for d in scores)}
        return result


def run_checks(candidate, kit, *, baseline=None, output=None):
    """Return mandatory unit and official replay evidence for an exact snapshot."""
    _docker()
    candidate, kit = Path(candidate).absolute(), Path(kit).absolute()
    output = Path(output).absolute() if output is not None else None
    if output is not None:
        output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="astra-claude-check-") as temporary:
        workdir = Path(temporary)
        bot = workdir / "controller"
        trusted_kit = workdir / "kit"
        _copy_files(candidate, bot, CONTROLLER_FILES)
        _copy_files(ROOT, bot, TEST_FILES)
        _copy_files(kit, trusted_kit, KIT_FILES)
        image = _image()

        name = f"astra-claude-{uuid.uuid4().hex}"
        unit, log = _check(_sandbox(name, bot, trusted_kit, image, unit=True),
                           name, workdir, output, "unit")
        count = re.search(r"^Ran (\d+) tests? in ", log, re.MULTILINE)
        unit["tests"] = int(count.group(1)) if count else 0
        unit["ok"] = unit["ok"] and unit["tests"] > 0

        name = f"astra-claude-{uuid.uuid4().hex}"
        checker = [sys.executable, "-I", str(trusted_kit / "check" / "check.py"), "--map-dir", "/arena"]
        sandbox = _sandbox(name, bot, trusted_kit, image)
        docker, log = _check([*checker, "--", *sandbox], name, workdir, output, "docker")
        timing = re.search(
            r"^observations: (\d+)  answered in time: (\d+)  missed the [^\n]*?: (\d+) ",
            log, re.MULTILINE,
        )
        if timing:
            docker.update(zip(("observations", "answered_in_time", "missed"), map(int, timing.groups())))
        docker["ok"] = docker["ok"] and docker.get("observations") == 300 and log.rstrip().endswith("\nPASS")
        ok = unit["ok"] and docker["ok"]
        paired = {"status": "not_requested" if baseline is None else "skipped"}
        if ok and baseline is not None:
            try:
                paired = _paired(Path(baseline).absolute(), bot, trusted_kit, workdir, image)
            except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
                paired = {"status": "failed", "problem": type(exc).__name__}
                ok = False
        return {"ok": ok, "unit": unit, "docker": docker, "paired": paired}
