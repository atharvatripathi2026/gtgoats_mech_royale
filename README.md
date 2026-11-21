# Astra

Astra pilots one mech in the Builders Mech Royale competition. It starts moving toward the next circle before the current one closes, looks for cover while healing, and keeps its torso on an attacker while its legs move independently.

## How it plays

- **Movement.** At startup Astra reads the mounted terrain and solid prisms into a three-metre grid. It routes around buildings, uses passages with enough headroom, and saves jets for obstructions and forced rooftop finishes. After early rooftop camping scored 3.23, the adaptive candidate returned to the ground policy that scored 3.60.
- **Survival.** The bot estimates travel time to the next circle, reserves energy for escapes, and uses nearby cover to break a pursuer’s line of sight. It looks for accessible cubes, weapon pickups and uncontested supply drops and evaluates upgrade offers using the live rule definitions.
- **Combat.** Astra leads moving targets and tracks the actual torso angle before firing. It can keep shooting while retreating, time a charged laser release, lob mortar shells, and conserve lightning energy when a target is outside the cone. A wounded mech can disengage long enough to regenerate.

## Runtime and attribution

The root Dockerfile pins CPython 3.13.18 on Debian Trixie by digest. The bot uses only the Python standard library. The JSON-lines transport and type definitions in `mechfight.py` come from the official Builders starter kit. The kit's example and Dockerfile supplied the starting layout. The policy, navigation and tests were developed for this competition. The referee mounts the organizer's map at runtime.

[Organizer’s starter kit and protocol](https://www.joinbuilders.org/buildathon/tracks/builders)

## Run the official replay check

From the extracted kit directory, set `BOT` to the absolute path to this checkout. Make the map readable by the container user.

```sh
chmod -R a+rX arena
python3 check/check.py -- python3 -u "$BOT/bot.py"
docker build --platform linux/amd64 -t mech-royale-bot "$BOT"
python3 check/check.py --map-dir /arena -- docker run --rm -i --network none --cpus 1 --memory 512m --read-only --tmpfs /tmp:rw,size=64m --user 65534:65534 -v "$PWD/arena:/arena:ro" mech-royale-bot
```

From the bot checkout, run the focused checks against the same starter kit. Set the optional trace flag only when inspecting individual decisions locally.

```sh
MECHFIGHT_KIT=/path/to/mechfight-kit python3 -m unittest discover -s tests
MECHFIGHT_TRACE=1 python3 /path/to/mechfight-kit/check/check.py -- python3 -u bot.py
```

The checker replays 300 observations and measures response timing. The competition site runs the 48 matches that determine a practice score. Use `git rev-parse HEAD` to identify the candidate for submission.

## Official practice runs

The house squad cooperates in practice. The top 16 finalists play one another on new seeds. Each match awards `16 - place` points.

| Tested commit | Mean placement points | Matches |
| --- | ---: | ---: |
| [`4cb4a9e`](https://github.com/atharvatripathi2026/gtgoats_mech_royale/commit/4cb4a9ea753e8df3744a9ba8d44053068e64e535) | 3.60 | 48 |
| [`9e59bbf`](https://github.com/atharvatripathi2026/gtgoats_mech_royale/commit/9e59bbfd46f562dbb88d0a4377dc333ce2f8c273) | 3.23 | 48 |
| [`ce73f3e`](https://github.com/atharvatripathi2026/gtgoats_mech_royale/commit/ce73f3e213a1c7bcc1fb65a90b4edf6e76133c13) | 3.65 | 48 |
| [`03a8f93`](https://github.com/atharvatripathi2026/gtgoats_mech_royale/commit/03a8f93fb36afa5db4a08f211d1d1aa6dcbcae8e) | 3.71 | 48 |

## Decision records

Each played observation produces a JSON-lines record with its tick, observed state and events, movement mode and goal, decision reason, combat target, learned context, and the action sent. The final record includes the referee’s placement and kill count when it sends `end`. Match-local adaptation starts fresh at each `hello`.

The scorer runs with a read-only image, a private 64 MB `/tmp`, and no network. It displays the practice score and may display a scorer message. The team page does not provide the match filesystem. The files below are available from runs you control.

```sh
# From the extracted starter kit, with BOT set to this checkout:
mkdir -p "$PWD/astra-logs"
MECHFIGHT_LOG_DIR="$PWD/astra-logs" python3 check/check.py -- python3 -u "$BOT/bot.py"
# From the bot checkout, inspect an individual log:
python3 -m training.review /path/to/match.jsonl --last 10
```

Use `MECHFIGHT_LOG_RAW=1` for full local observations. The default compact trace keeps space available for the whole match. For a local Docker run, bind a directory writable by uid 65534 at `/tmp/mechfight-logs`. The official replay uses prerecorded observations; its terminal result belongs to the recording.

## Train and validate a policy locally

The trainer plays closed-loop local games using the kit's rule values. The arena changes in response to actions, reports the outcome, and writes decision and event logs. The trainer tries bounded changes to `policy.json`, compares them on paired seeds, and reserves independent seeds to check whether a candidate generalizes. The official 48-match aggregate remains the comparison for competition entries.

```sh
python3 -m training.tune --kit /path/to/mechfight-kit \
    --output-dir /tmp/astra-training --rounds 3 --train-seeds 3 \
    --validation-seeds 3 --test-seeds 4 --apply
```

For two different gameplay commits, use `python3 -m training.compare --help` to run paired matches on generated layouts and the kit's campus. Add `--traces` to keep the decisions and outcomes from every game.

## GT Goats practice submissions

The team's Claude Max account can run a second candidate producer alongside Codex. [Teammate setup](CLAUDE_WORKER.md)

The Chrome helper submits tested commits from this team's public candidate queue through the Builders practice form. It runs while the computer is awake and the signed-in track tab is open. It stops at 11 a.m. Eastern on Sunday, November 22, 2026.

1. Download and unzip the [practice helper](https://raw.githubusercontent.com/atharvatripathi2026/gtgoats_mech_royale/388b71763dbf00affe6fc4324c18f382b77eb826/gt-goats-practice-helper.zip).
2. In desktop Chrome, open `chrome://extensions`, turn on **Developer mode**, choose **Load unpacked**, and select the unzipped folder containing `manifest.json`.
3. Open or refresh the [Builders practice form](https://www.joinbuilders.org/buildathon/tracks/builders#submit) in that Chrome profile. Sign in for GT Goats if prompted. Click **Start GT Goats submissions** in the panel at the bottom right. Use **Stop** there to pause.

The helper reads the site's remaining allowance, waits for a previous run to finish, and spaces its own attempts at least 15 minutes apart. With several candidates available, it gives preference to changes based on higher-scoring entries. Every fourth attempt tries the oldest eligible candidate. Scores, receipts and scorer messages are kept in this Chrome profile and are available under **Export results**. If the site never acknowledges a click, the panel lets you check the official history, stop, and retire that commit before resuming.

Three agents review each new candidate from the perspectives of survival and positioning, combat and equipment, and opponent modeling and validation. After they test a frozen commit, record each actual verdict and its evidence in `votes.json`. A revision gets a new review of its exact commit. The publisher requires all three approvals and stores them with the entry so later runs can read the reasons.

```sh
python3 -m training.publish_candidate --commit FULL_SHA --reviews votes.json --summary 'Gameplay change and test results'
```

```json
{
  "commit": "FULL_SHA",
  "votes": {
    "survival": {"decision": "approve for practice", "reason": "Survival reviewer's finding"},
    "combat": {"decision": "approve for practice", "reason": "Combat reviewer's finding"},
    "validation": {"decision": "approve for practice", "reason": "Validation reviewer's finding"}
  }
}
```

[Candidate queue](https://github.com/atharvatripathi2026/gtgoats_mech_royale/blob/practice-queue/queue.json)
