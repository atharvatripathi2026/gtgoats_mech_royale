"""Bounded within-match feedback for isolated, open-ground engagements."""
import json
import math
from collections import deque
from pathlib import Path

DEFAULT_POLICY = {"engage_range_m": 78.0, "retreat_bias": 0.40, "pressure_gain": 1.30,
                  "loot_priority": 1.0}
POLICY_BOUNDS = {"engage_range_m": (40.0, 115.0), "retreat_bias": (0.0, 0.65),
                 "pressure_gain": (0.3, 2.5), "loot_priority": (.65, 2.0)}


def validate_policy(mapping):
    """Accept complete or partial overrides. Reject invalid search candidates."""
    if not isinstance(mapping, dict) or mapping.keys() - POLICY_BOUNDS.keys():
        raise ValueError("Unknown policy structure or parameter")
    policy = dict(DEFAULT_POLICY)
    for name, value in mapping.items():
        low, high = POLICY_BOUNDS[name]
        if type(value) not in (int, float) or not math.isfinite(value) or not low <= value <= high:
            raise ValueError(f"{name} must be a finite number between {low} and {high}")
        policy[name] = float(value)
    return policy


def load_policy(path=None):
    file = Path(path) if path is not None else Path(__file__).with_name("policy.json")
    with file.open(encoding="utf-8") as stream:
        return validate_policy(json.load(stream))


class AdaptivePolicy:
    """Credit contiguous, evidenced action intervals and remember outcomes by opposing loadout.

    Each estimate is a decaying, bounded sum of fractional HP advantages. Decisions preserve
    the underlying strafe sign and adjust radial speed only when the alternative is safe.
    """
    def __init__(self, hello, nav=None, policy=None):
        self.policy = load_policy() if policy is None else validate_policy(policy)
        self.nav = nav
        self.rules = hello.get("config", {})
        match = self.rules.get("match", {})
        self.stride = match.get("decide_every", 2)
        self.dt = self.stride / max(1, match.get("tick_hz", 20))
        self.side = 1 if hello.get("seed", 0) % 2 else -1
        self.values = {context: {"press": 0.0, "space": 0.0} for context in ("gun", "armed")}
        self.confirmed = 0
        self.samples = {key: {"press": 0, "space": 0} for key in self.values}
        self.probed = set()
        self.staged = self.pending = None
        self.arm = self.context = self.target = None
        self.choose_at = -1.0
        self.shots = deque(maxlen=32)
        self.reason = "new_match"
        self.credited = False
        self.reward = 0.0
        self.feedback = {}

    def diagnostics(self):
        estimates = self.values.get(self.context, {})
        return {"context": self.context, "arm": self.arm, "reason": self.reason,
                "credited": self.credited, "reward": round(self.reward, 5),
                "estimates": {k: round(v, 5) for k, v in estimates.items()},
                "evidence": self.confirmed, "feedback": dict(self.feedback),
                "probed": sorted(self.probed), "arm_evidence": self.samples}

    def sent(self, tick, action, on_time=True, applied=False):
        """Call after a valid flush; applied=True is for a simulator with explicit application."""
        stage = self.staged
        if stage is None or tick != stage["tick"]:
            return
        self.staged = self.pending = None
        if not on_time or action.get("tick", tick) != tick:
            self.shots.clear()
            return
        motion = action.get("move") or (0, 0)
        if len(motion) != 2 or math.hypot(*motion) < 0.3 or action.get("jump"):
            self.shots.clear()
            return
        stage["move"] = tuple(motion)
        stage["speed"] = stage["sprint"] if action.get("boost") else stage["walk"]
        stage["applied"] = bool(applied)
        triggers = action.get("fire") or ()
        stage["shots"] = [shot for i, shot in enumerate(stage["slots"])
                          if shot is not None and bool(i < len(triggers) and triggers[i]) == shot[2]]
        self.pending = stage

    def _observed_motion(self, prior, me):
        # A constant velocity could simply be the server coasting an older action.
        # Require a measured change towards the command; a simulator can acknowledge it.
        if prior["applied"]:
            return True
        if not me.get("grounded", True):
            return False
        px, py = prior["pos"]
        if math.hypot(me["pos"][0]-px, me["pos"][1]-py) < 0.06:
            return False
        ux, uy = prior["move"]
        mag = max(1, math.hypot(ux, uy))
        vx, vy = prior["vel"]
        ax, ay = ux * prior["speed"] / mag - vx, uy * prior["speed"] / mag - vy
        nx, ny = (me.get("vel") or (0, 0))[:2]
        dx, dy = nx - vx, ny - vy
        gain, intended = math.hypot(dx, dy), math.hypot(ax, ay)
        if gain < .22 or intended < .25 or gain > prior["accel"] * self.dt * 1.45 + .4:
            return False
        return dx * ax + dy * ay > .82 * gain * intended

    def _learn(self, obs):
        self.credited, self.reward, self.feedback = False, 0.0, {}
        prior, self.pending = self.pending, None
        if prior is None:
            self.shots.clear()
            return
        t, me = obs.get("t", 0), obs["self"]
        elapsed = t - prior["t"]
        if (obs["tick"] != prior["tick"] + self.stride or abs(elapsed - self.dt) > self.dt * .30
                or not self._observed_motion(prior, me)):
            self.shots.clear()
            return
        context, arm, target = prior["context"], prior["arm"], prior["target"]
        sequence = (context, arm, target)
        # Slow shots can land after a switch. Match the weapon and its arrival
        # window to an eligible trigger in a confirmed interval. Discard hits
        # when two different policies could have caused them.
        for kind, travel, _ in prior["shots"]:
            tolerance = self.dt * 1.3 + .20 * travel
            self.shots.append((sequence, kind, prior["t"] + travel - tolerance,
                               prior["t"] + travel + tolerance + self.dt))
        arriving = {}
        for origin, kind, start, end in self.shots:
            if start <= t <= end:
                arriving.setdefault(kind, set()).add(origin)
        killed_target = False
        dealt = taken = zone = kills = 0.0
        for event in obs.get("events") or ():
            kind = event.get("type")
            amount = max(0, event.get("amount", 0))
            if kind == "damaged":
                if event.get("weapon") == "zone":
                    zone += amount
                else:
                    taken += amount
            elif (kind == "hit" and event.get("target") == target
                  and arriving.get(event.get("weapon")) == {sequence}):
                dealt += amount
            elif kind == "kill" and event.get("target") == target:
                killed_target = True
        if dealt and killed_target:
            kills = 1
        maximum = max(1, me.get("max_hp", prior["max_hp"]))
        cubes = max(0, me.get("cubes", 0) - prior["cubes"])
        hp_gain = me.get("hp", prior["hp"]) - prior["hp"]
        regen_rate = self.rules.get("mech", {}).get("regen_per_s", 45)
        regen = max(0, min(regen_rate * elapsed, hp_gain)) if not (cubes or taken or zone or dealt) else 0.0
        if not me.get("in_zone", True):
            zone = max(zone, elapsed * obs.get("zone", {}).get("dps", 0))
        # A placement bot values its own health more than equal damage to one
        # of 15 opponents. Cubes and repair are useful only when actually gained.
        cube_value = self.rules.get("cubes", {}).get("hp_per_cube", .04)
        self.reward = max(-.25, min(.25, (.78 * dealt - 1.45 * taken - 1.7 * zone + .9 * regen) /
                                   maximum + cube_value * min(3, cubes) + .09 * min(1, kills)))
        self.feedback = {"hit": round(dealt, 1), "hurt": round(taken, 1), "zone": round(zone, 1),
                         "regen": round(regen, 1), "cubes": cubes, "kills": int(kills)}
        self.confirmed += 1
        self.samples[context][arm] += 1
        self.credited = True
        for option in self.values[context]:
            self.values[context][option] *= math.exp(-elapsed / 14)
        estimate = self.values[context][arm] + self.policy["pressure_gain"] * self.reward
        self.values[context][arm] = max(-.45, min(.45, estimate))

    def _near_projectile(self, obs):
        me = obs["self"]
        x, y, z = me["pos"]
        vx, vy, vz = (me.get("vel") or (0, 0, 0))
        stats = me.get("stats") or {}
        for shot in obs.get("projectiles") or ():
            p, v = shot.get("pos"), shot.get("vel")
            if not p or not v:
                continue
            dx, dy = p[0] - x, p[1] - y
            wx, wy = v[0] - vx, v[1] - vy
            mortar = shot.get("kind") == "mortar"
            gravity = 0.0
            if mortar:
                rules = self.rules.get("weapons", {}).get("mortar", {})
                gravity = max(.1, rules.get("gravity", 22))
                delta = v[2] * v[2] + 2 * gravity * (p[2] - z)
                if delta >= 0:
                    landing = (v[2] + math.sqrt(delta)) / gravity
                    blast = rules.get("splash_radius", 7) + stats.get("radius", 2.5) + 3
                    if 0 <= landing <= 1.45 and math.hypot(dx + wx*landing, dy + wy*landing) <= blast:
                        return True
            eta = -(dx * wx + dy * wy) / max(1, wx * wx + wy * wy)
            if (0 <= eta < .6 and math.hypot(dx + wx * eta, dy + wy * eta) < stats.get("radius", 2.5) + 2
                    and -1 < p[2] - z + (v[2] - vz) * eta - .5 * gravity * eta * eta < stats.get("height", 9) + 1):
                return True
        return False

    @staticmethod
    def _zone_room(obs, radius):
        """Reserve enough time to reach the new circle and room for one local maneuver."""
        zone, pos = obs.get("zone") or {}, obs["self"]["pos"][:2]
        center, r = zone.get("center"), zone.get("radius")
        target, nr = zone.get("next_center"), zone.get("next_radius")
        if center is None or r is None or target is None or nr is None:
            return False
        margin = radius + 16
        if math.dist(pos, center) + margin >= r:
            return False
        if math.dist(pos, target) + margin < nr:
            return True
        t = obs.get("t", 0)
        remaining = max(0, zone.get("shrink_end", t) - t)
        wait = max(0, zone.get("shrink_start", t) - t)
        speed = (obs["self"].get("stats") or {}).get("walk_speed", 11.7)
        # Test an 8s look-ahead and budget the detour at reduced walking speed.
        # Checking only the final circle was prematurely blocking during long holds.
        excess = max(0, math.dist(pos, target) - max(0, nr - margin))
        if remaining < 9 + (excess + 15) / max(1, speed * .55):
            return False
        u = max(0, min(1, (8 - wait) / max(.01, remaining - wait)))
        forecast = (center[0] + u * (target[0] - center[0]), center[1] + u * (target[1] - center[1]))
        return math.dist(pos, forecast) + margin < r + u * (nr - r)

    def _available_shots(self, me, dist):
        result = []
        for weapon in me.get("weapons") or ():
            shot = None
            if weapon and weapon.get("cooldown", 0) < self.dt and not weapon.get("reload", 0):
                kind = weapon.get("kind")
                base = self.rules.get("weapons", {}).get(kind, {})
                stats = weapon.get("stats") or base
                if kind == "gun" and weapon.get("ammo", 1) > 0:
                    shot = (kind, dist / max(1, stats.get("speed", 252)), True)
                elif kind == "mortar":
                    horizontal = stats.get("speed", 72) * math.cos((me.get("aim") or (0, 0))[1])
                    shot = (kind, dist / max(1, horizontal), True)
                elif kind == "lightning" and dist <= stats.get("range", 45):
                    shot = (kind, 0.0, True)
                elif kind == "laser" and weapon.get("charge", 0) >= stats.get("min_charge", .15):
                    shot = (kind, 0.0, False)
            result.append(shot)
        return result

    def decide(self, obs, plan):
        self._learn(obs)
        self.staged = None
        me, t = obs["self"], obs.get("t", 0)
        pos = me["pos"]
        stats = me.get("stats") or {}
        radius = stats.get("radius", 2.5)
        self.reason = "protected_goal"
        if (plan.get("mode") not in ("hold", "zone", "evade", "hunt", "hunter")
                or len(plan["goal"]) > 2 or not me.get("grounded", True)
                or me.get("hp", 0) < .44 * me.get("max_hp", 1400)
                or not me.get("in_zone", True)):
            return plan
        if plan.get("dodge") or self._near_projectile(obs):
            self.reason = "incoming_projectile"
            return plan
        if plan.get("zone_urgency", 0) >= .35 or not self._zone_room(obs, radius):
            self.reason = "zone_margin"
            return plan
        nearby = []
        for enemy in obs.get("mechs") or ():
            if enemy.get("kind") != "mech" or not enemy.get("pos"):
                continue
            p = enemy["pos"]
            d = math.hypot(pos[0] - p[0], pos[1] - p[1])
            if d < 170:
                nearby.append((d, enemy))
        if len(nearby) != 1:
            self.reason = "opponent_count"
            return plan
        d, enemy = nearby[0]
        p, target = enemy["pos"], enemy.get("id")
        if (target is None or not max(36, 8 * radius) < d < min(145, self.policy["engage_range_m"] + 55)
                or enemy.get("charging") or ("lightning" in (enemy.get("weapons") or ()) and d < 65)):
            self.reason = "engagement_range"
            return plan
        if self.nav and (abs(pos[2] - self.nav.ground(*pos[:2])) > 3 or not self.nav.line_clear(
                (*pos[:2], pos[2] + stats.get("eye_height", 8)), (*p[:2], p[2] + 4.5))):
            self.reason = "covered"
            return plan
        bx, by = (p[0]-pos[0])/d, (p[1]-pos[1])/d
        gx, gy = plan["goal"][0]-pos[0], plan["goal"][1]-pos[1]
        length = math.hypot(gx, gy)
        lateral = (bx * gy - by * gx) / max(1, length)
        # Preserve intentional retreats, route commitments, and precise turns.
        if length > 3 and abs(lateral) < .48:
            self.reason = "committed_route"
            return plan
        if self.nav and length > 3:
            look = min(1, 17 / length)
            old = pos[0] + gx * look, pos[1] + gy * look
            if not self.nav.line_clear((*p[:2], p[2] + 7), (*old, self.nav.ground(*old) + 5)):
                self.reason = "reachable_cover"
                return plan
        context = "armed" if set(enemy.get("weapons") or ()) - {"gun"} else "gun"
        hp = me.get("hp", 0) / max(1, me.get("max_hp", 1400))
        other = enemy.get("hp", 1400) / max(1, enemy.get("max_hp", 1400))
        if self.arm is None or self.context != context or self.target != target or t >= self.choose_at:
            prior = .035 * (hp - other) + .028 * (d > self.policy["engage_range_m"])
            if self.context == context and self.target == target and self.arm is not None:
                prior += .006 if self.arm == "press" else -.006
            self.arm = "press" if self.values[context]["press"] + prior >= self.values[context]["space"] else "space"
            self.context, self.target, self.choose_at = context, target, t + .85
        alternative = "space" if self.arm == "press" else "press"
        probe = (context not in self.probed and self.samples[context][self.arm] >= 3
                 and self.samples[context][alternative] == 0 and abs(self.values[context][self.arm]) < .11
                 and hp >= .8 and d >= 58 and me.get("energy",100) >= .48*me.get("max_energy",100))
        arm = alternative if probe else self.arm
        # A signed radial component changes separation without undoing the
        # strafe direction chosen by the existing projectile/cover policy.
        old_radial = (bx * gx + by * gy) / max(1, length)
        if arm == "space":
            radial = max(-.77, min(-.14, old_radial - self.policy["retreat_bias"]))
        else:
            desired = max(-.25, min(.40, (d-self.policy["engage_range_m"])*.012))
            radial = .55 * old_radial + .45 * desired
        tangent = math.copysign(math.sqrt(max(0, 1-radial*radial)), lateral if abs(lateral) > .1 else self.side)
        step = min(15, max(8, stats.get("walk_speed", 11.7)))
        ux, uy = radial * bx - tangent * by, radial * by + tangent * bx
        end = pos[0] + step * ux, pos[1] + step * uy
        if self.nav:
            last_z = pos[2]
            for f in (.25, .5, .75, 1.0):
                point = (pos[0] + f * step * ux, pos[1] + f * step * uy)
                z = self.nav.ground(*point)
                if not self.nav.walkable(*point, radius) or abs(z-last_z) > step*.25*.85:
                    self.reason = "unsafe_footing"
                    return plan
                last_z = z
            opposing_aim = enemy.get("aim")
            if (plan["mode"] == "hold" and length < 2.5 and opposing_aim
                    and "gun" in (enemy.get("weapons") or ())):
                origin = (*p[:2], p[2] + 7)
                height = stats.get("height", 9)
                exposed_bearing = math.atan2(end[1] - p[1], end[0] - p[0])
                yaw_gap = abs((exposed_bearing - opposing_aim[0] + math.pi) % math.tau - math.pi)
                turn_allowance = self.dt * self.rules.get("mech", {}).get("turn_rate", 4)
                exposed_range = math.hypot(end[0] - p[0], end[1] - p[1])
                can_turn = yaw_gap <= turn_allowance + math.atan2(radius, exposed_range)

                def covered(point, floor):
                    return all(not self.nav.line_clear(origin, (*point, floor + height * ratio))
                               for ratio in (.43, .73))

                if can_turn and covered(pos[:2], pos[2]) and not covered(end, self.nav.ground(*end)):
                    self.reason = "hold_protected_ground"
                    return plan
        if probe:
            self.probed.add(context)
            self.arm, self.choose_at = arm, t + .6
        self.reason = "engagement"
        self.staged = {"tick": obs["tick"], "t": t, "context": context, "arm": self.arm,
                       "target": target, "dist": d, "pos": tuple(pos[:2]),
                       "vel": tuple((me.get("vel") or (0,0))[:2]),
                       "hp": me.get("hp", 0), "max_hp": me.get("max_hp", 1400),
                       "slots": self._available_shots(me, d),
                       "cubes": me.get("cubes", 0), "walk": stats.get("walk_speed", 11.7),
                       "sprint": stats.get("boost_speed", 19.5), "accel": stats.get("ground_accel", 58.5)}
        return dict(plan, goal=end)
