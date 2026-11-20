"""Placement-oriented navigation objectives for the Mech Royale game."""
import math
import random


def distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def clip(value):
    return max(0.0, min(1.0, value))


def disc_point(pos, center, radius):
    """Nearest point in a circle to pos, including a circle of radius zero."""
    d = distance(pos, center)
    scale = min(1, max(0, radius) / max(d, 0.001))
    return (center[0] + (pos[0] - center[0]) * scale,
            center[1] + (pos[1] - center[1]) * scale)


class Survival:
    def __init__(self, hello, nav=None):
        self.rules = hello.get("config", {})
        self.nav = nav
        self.turn_side = 1 if hello.get("seed", 0) % 2 else -1
        self.rng = random.Random(hello.get("seed", 0))
        self.weave_side = self.turn_side
        self.reverse_at = 0.7
        self.check_cover_at = -1
        self.open_ground = False
        self.pursuer = None
        self.last_contact = (-100.0, 0.0, 0.0)
        self.sight = {}
        self.loot = {}
        self.chase_id = None
        self.chase_record = (0, 0)
        self.skip_until = {}
        self.evade_goal = None
        self.evade_until = -1
        self.boosting = False
        self.cover_goal = None
        self.cover_until = -1

    def _zone(self, obs, pos, speed, radius):
        zone = obs.get("zone") or {}
        t = obs.get("t", 0)
        c = zone.get("center", pos)
        r = zone.get("radius", 560)
        nc = zone.get("next_center", c)
        nr = zone.get("next_radius", r)
        until = max(0.0, zone.get("shrink_end", t + 100) - t)
        wait = max(0.0, zone.get("shrink_start", t) - t)
        # The published current circle already includes all shrink up to t.
        u = clip((8.0 - wait) / max(0.01, until - wait))
        fc = (c[0] + u * (nc[0] - c[0]), c[1] + u * (nc[1] - c[1]))
        fr = r + u * (nr - r)
        margin = min(max(10.0, radius + 9), fr * 0.30)
        future_safe = max(0.0, nr - min(radius + 14, nr * 0.33))
        path_time = max(0.0, distance(pos, nc) - future_safe) / max(1, speed * 0.57)
        shortfall = distance(pos, fc) - (fr - margin)
        urgency = max(clip((path_time + 7 - until) / 7) if path_time > 0 else 0,
                      clip((shortfall + 2) / 18) if shortfall > 0 else 0)
        if obs.get("self", {}).get("in_zone") is False or distance(pos, c) > r + 0.1:
            urgency = 1.0
        # Approach from our current side. Forcing every spawn to the center
        # crowds vision lines and gives up uncontested loot near the flank.
        anchor = disc_point(pos, nc, min(future_safe, nr * 0.72))
        if nr < 20 and self.nav and not self.nav.walkable(*anchor, radius):
            roof = self.nav.surface(*anchor)
            if roof - pos[2] <= 45:
                anchor = (*anchor, roof)
        return anchor, urgency, (fc, fr), (nc, nr), until

    def _enemies(self, obs, now, pos):
        """The server itself tracks live enemy positions during vision memory."""
        me = obs["self"]
        eye = me.get("stats", {}).get("eye_height", 8)
        threats = []
        for enemy in obs.get("mechs") or ():
            if enemy.get("kind") != "mech" or "pos" not in enemy:
                continue
            p = enemy["pos"]
            d = distance(pos, p)
            threats.append((d, enemy))
        threats.sort(key=lambda pair: pair[0])
        spotted = []
        strongest = 0.0
        bearing = None
        self.pursuer = None
        for d, enemy in threats[:5]:
            p = enemy["pos"]
            yaw = math.atan2(p[1] - pos[1], p[0] - pos[0])
            facing = math.cos(enemy.get("aim", [yaw])[0] - yaw - math.pi)
            key = enemy.get("id")
            when, visible = self.sight.get(key, (-9, True))
            if self.nav and now - when > 0.40:
                visible = self.nav.line_clear((p[0], p[1], p[2] + 7),
                                              (pos[0], pos[1], pos[2] + eye))
                self.sight[key] = now, visible
            power = clip((143 - d) / 105) * (0.62 + 0.38 * max(0.0, facing))
            if enemy.get("charging") and facing > 0.95 and d < 200:
                power = max(power, 0.90)
            has_arc = "lightning" in (enemy.get("weapons") or ())
            arc_range = self.rules.get("weapons", {}).get("lightning", {}).get("range", 45)
            if has_arc and d < arc_range + 8:
                power = max(power, 0.98)
            if not visible:
                power *= 0.45 if d < 30 else 0.10
            elif (30 < d < 160 and facing > 0.92 and not enemy.get("charging")
                  and "gun" in (enemy.get("weapons") or ())
                  and (len(threats) == 1 or threats[1][0] > 160)):
                self.pursuer = p
            if power > strongest:
                strongest, bearing = power, yaw
            spotted.append((p, power, d, visible))
        # Several opponents can sustain focus fire even at medium distances.
        pressure = min(1.0, strongest + 0.22 * (sum(a[1] for a in spotted) - strongest))
        signals = [(1.0, e["bearing"]) for e in obs.get("events") or ()
                   if e.get("type") == "damaged" and e.get("bearing") is not None
                   and e.get("weapon") not in ("npc", "zone")]
        for sound in obs.get("sounds") or ():
            kind = sound.get("kind")
            if sound.get("dist") != "near" or sound.get("bearing") is None:
                continue
            weight = {"lightning": 0.69, "laser_charge": 0.65, "laser": 0.60,
                      "mortar": 0.51, "gun": 0.44, "boost": 0.38, "step": 0.33}.get(kind, 0)
            if weight:
                signals.append((weight, sound["bearing"]))
        last, weight, direction = self.last_contact
        remembered = weight * clip(1 - (now - last) / 2.7)
        if signals:
            new, angle = max(signals)
            if new >= remembered:
                self.last_contact = now, new, angle
                remembered, direction = new, angle
        if remembered > pressure:
            pressure, bearing = remembered, direction
        return spotted, pressure, bearing

    def _dodge(self, obs, pos, radius):
        """Return a dangerous flight line, or an imminent shell impact point."""
        vx, vy, vz = list(obs["self"].get("vel") or [0, 0, 0])
        h = obs["self"].get("stats", {}).get("height", 9)
        mortar = self.rules.get("weapons", {}).get("mortar", {})
        best, dodge = -1, None
        for shot in obs.get("projectiles") or ():
            if "pos" not in shot or "vel" not in shot:
                continue
            x, y, z = shot["pos"]
            dx, dy = x - pos[0], y - pos[1]
            sx, sy, sz = shot["vel"]
            if shot.get("kind") == "mortar":
                gravity = max(0.1, mortar.get("gravity", 22))
                disc = sz * sz + 2 * gravity * (z - pos[2])
                if disc < 0:
                    continue
                eta = (sz + math.sqrt(disc)) / gravity
                landing = x + sx * eta, y + sy * eta
                if not (0 <= eta < 1.45) or distance(landing, (pos[0] + vx * eta, pos[1] + vy * eta)) > mortar.get("splash_radius", 7) + radius + 3:
                    continue
                item = ("blast", landing, eta, 0)
            else:
                ax, ay = sx - vx, sy - vy
                speed2 = ax * ax + ay * ay
                eta = -(dx * ax + dy * ay) / max(1, speed2)
                if not 0 < eta < 0.67 or math.hypot(dx + ax * eta, dy + ay * eta) > radius + 1.5:
                    continue
                height = z + (sz - vz) * eta - pos[2]
                if not -1 < height < h + 1:
                    continue
                angle = math.atan2(sy, sx)
                normal = (-math.sin(angle), math.cos(angle))
                offset = (dx + ax * eta) * normal[0] + (dy + ay * eta) * normal[1]
                item = ("line", normal, eta, offset)
            priority = (2 if item[0] == "blast" else 1) - eta * 0.5
            if priority > best:
                best, dodge = priority, item
        return dodge

    def _loot_goal(self, obs, now, pos, radius, health, foes, circle, final, until):
        me = obs["self"]
        held = {w.get("kind") for w in me.get("weapons", []) if w}
        cap = self.rules.get("cubes", {}).get("stat_cap", 10)
        power = me.get("cubes", 0)
        table = (("cubes", 52 if power < cap else 15),
                 ("pickups", 50 if len(held) < 2 else 0),
                 ("crates", 17 if health >= 0.78 and power < cap else 0))
        for field, value in table:
            if not value:
                continue
            for obj in obs.get(field) or ():
                if "id" not in obj or "pos" not in obj:
                    continue
                if field == "pickups" and obj.get("kind") in held:
                    continue
                self.loot[obj["id"]] = (now, obj["pos"], field, value)
        best_score, best = 0, None
        options = []
        for key, (seen, p, field, value) in list(self.loot.items()):
            if (now - seen > (8 if field in ("pickups", "cubes") else 4.5) or (now > seen and distance(p, pos) < 5)
                    or (field == "pickups" and len(held) >= 2)):
                del self.loot[key]
                continue
            if field == "crates" and (health < 0.78 or power >= cap):
                continue
            if field == "cubes" and power >= cap:
                value = 15
            options.append((key, p, field, value))
        for drop in obs.get("drops") or ():
            if drop.get("holder") not in (None, me.get("id")) or "pos" not in drop:
                continue
            if any(distance(p, drop["pos"]) < 49 for p, _, _, _ in foes):
                continue
            lands = drop.get("lands_in", 0)
            if lands > distance(pos, drop["pos"]) / 10 + 5:
                continue
            value = 46 + (1 - health) * 25 - 2 * max(0, lands - distance(pos, drop["pos"]) / 10)
            options.append((drop.get("id"), drop["pos"], "drop", value))
        for key, p, field, value in options:
            if now < self.skip_until.get(key, -1):
                continue
            d = distance(p, pos)
            if d > (100 if field in ("drop", "pickups", "cubes") else 72) or distance(p, circle[0]) > max(0, circle[1] - min(radius + 3, circle[1]*0.25)):
                continue
            # A cube on a roof is unreachable from directly below. A long
            # roof climb costs both time and the reserve for the next escape.
            if p[2] - pos[2] > 5 and (not self.nav or p[2] - self.nav.ground(*p[:2]) > 5):
                continue
            if pos[2] - p[2] > 12 and d < 8:
                continue
            future_over = max(0.0, distance(p, final[0]) - max(0, final[1] - 8))
            if d / 7 + future_over / 6 + 7 > until and future_over > 0:
                continue
            if any(power > 0.16 and distance(p, fp) + 5 < min(fd, 65)
                   for fp, power, fd, _ in foes):
                continue
            score = value - d * 0.48 + (3.5 if key == self.chase_id else 0)
            if score > best_score:
                best, best_score = (key, p, field, d), score
        if not best:
            self.chase_id = None
            return None
        key, p, kind, d = best
        if key != self.chase_id or d < self.chase_record[1] - 2.5:
            self.chase_record = now, d
        self.chase_id = key
        if now - self.chase_record[0] > (12 if kind == "drop" else 6.5):
            self.skip_until[key] = now + 14
            self.chase_id = None
            return None
        if kind == "drop":
            drop = next(o for o in obs["drops"] if o.get("id") == key)
            if d < max(1, drop.get("radius", 8) - 2.0):
                return tuple(pos[:2]), "capture", key
        if kind == "crates" and d < 17:
            return tuple(pos[:2]), "farm", key
        return tuple(p[:2]), ("farm" if kind == "crates" else "loot"), key

    def _evade(self, now, pos, radius, height, foes, bearing, dodge, anchor, circle, urgency):
        if self.evade_goal and now < self.evade_until and dodge is None and distance(pos, self.evade_goal) > 4:
            return self.evade_goal
        # Probe lateral routes as well as retreats. A single opponent tracking
        # directly along a straight retreat can hit every shot.
        base = bearing if bearing is not None else math.atan2(anchor[1] - pos[1], anchor[0] - pos[0])
        step = min(24, max(7, circle[1] * 0.48))
        candidates = []
        visible = [f for f in foes if f[3] and f[1] > 0.12]
        for i in range(12):
            angle = base + i * math.tau / 12
            dx, dy = math.cos(angle), math.sin(angle)
            end = pos[0] + step * dx, pos[1] + step * dy
            if self.nav and not self.nav.walkable(*end, radius):
                continue
            drift = distance(pos, anchor) - distance(end, anchor)
            score = drift * (0.12 + urgency * 1.5)
            score -= 3.0 * max(0, distance(end, circle[0]) - circle[1] + min(3, circle[1] * 0.2))
            if bearing is not None:
                lateral = math.sin(angle - bearing)
                score += -5.0 * math.cos(angle - bearing) + 13.0 * abs(lateral) + 1.2 * lateral * self.turn_side
            for p, weight, old, _ in foes:
                score += weight * (distance(end, p) - old) * 0.56
            if self.evade_goal:
                score += max(0, step - distance(end, self.evade_goal)) * 0.14
            if dodge:
                kind, vector = dodge[:2]
                if kind == "blast":
                    score += 2 * (distance(end, vector) - distance(pos, vector))
                else:
                    score += 28 * abs(dx * vector[0] + dy * vector[1])
            candidates.append((score, end))
        candidates.sort(reverse=True)
        # Expensive ray probes only for the best three legal escapes and the
        # primary attacker. Hiding while staying in the circle supports regen.
        if self.nav and visible:
            shooter = max(visible, key=lambda item: item[1])[0]
            for i, (score, end) in enumerate(candidates[:3]):
                z = self.nav.ground(*end)
                if not self.nav.line_clear((shooter[0], shooter[1], shooter[2] + 7),
                                           (end[0], end[1], z + height * 0.75)):
                    candidates[i] = score + 29, end
        if candidates:
            self.evade_goal = max(candidates)[1]
        else:
            self.evade_goal = anchor
        self.evade_until = now + 0.50
        return self.evade_goal

    def _finish_goal(self, obs, foes, circle, radius, health, fallback):
        """Strafe inward for a finishing shot on one exposed, badly hurt opponent."""
        if len(foes) != 1 or health <= .60:
            return fallback
        pos, _, d, visible = foes[0]
        me = obs["self"]
        here = me["pos"]
        if not visible or not 30 < d < 105:
            return fallback
        enemy = next(e for e in obs["mechs"] if e.get("kind") == "mech")
        if "hp" not in enemy or "max_hp" not in enemy:
            return fallback
        enemy_health = enemy["hp"] / max(1, enemy["max_hp"])
        if enemy_health >= .5 * health or enemy.get("charging"):
            return fallback
        dx, dy = (pos[0] - here[0]) / d, (pos[1] - here[1]) / d
        side = 1 if me["id"] % 2 else -1
        for sign in (side, -side):
            end = (here[0] + 13 * (.62 * dx - .78 * dy * sign),
                   here[1] + 13 * (.62 * dy + .78 * dx * sign))
            if distance(end, circle[0]) > circle[1] - radius - 7:
                continue
            if self.nav:
                if not self.nav.walkable(*end, radius):
                    continue
                sight = (*end, self.nav.ground(*end) + me.get("stats", {}).get("eye_height", 8))
                if not self.nav.line_clear(sight, (*pos[:2], pos[2] + 4.5)):
                    continue
            return end
        return fallback

    def _shelter(self, now, pos, radius, height, final):
        """Wait behind nearby cover facing the crowded side of the circle."""
        center, ring = final
        if not self.nav or ring < 32 or pos[2] > self.nav.ground(*pos[:2]) + 3:
            return tuple(pos[:2])
        if self.cover_goal is not None and now < self.cover_until:
            return self.cover_goal
        yaw = math.atan2(center[1] - pos[1], center[0] - pos[0])
        samples = []
        for angle in (0, -0.65, 0.65):
            dx, dy = math.cos(yaw + angle), math.sin(yaw + angle)
            x, y = pos[0] + dx * 52, pos[1] + dy * 52
            samples.append((x, y, self.nav.surface(x, y) + 7))

        def quality(point):
            eyes = (*point, self.nav.ground(*point) + height * 0.76)
            return sum(not self.nav.line_clear(source, eyes) for source in samples)

        best = tuple(pos[:2])
        score = quality(best)
        if score < 3:
            for step in (12, 25):
                for i in range(8):
                    a = yaw + i * math.tau / 8
                    p = (pos[0] + step * math.cos(a), pos[1] + step * math.sin(a))
                    if distance(p, center) > ring * 0.80 or not self.nav.walkable(*p, radius):
                        continue
                    q = quality(p) - step * 0.018
                    if q > score:
                        best, score = p, q
        self.cover_goal, self.cover_until = best, now + 4.5
        return best

    def _weave(self, obs, goal, radius, height, dodge):
        """Vary transverse velocity against a lone gun tracking us in the open."""
        pos, shooter, now = obs["self"]["pos"], self.pursuer, obs.get("t", 0)
        d = distance(pos, shooter)
        bx, by = (shooter[0] - pos[0]) / d, (shooter[1] - pos[1]) / d
        dx, dy = goal[0] - pos[0], goal[1] - pos[1]
        travel = math.hypot(dx, dy)
        if travel < 5:
            return goal
        radial = (dx * bx + dy * by) / travel
        lateral = abs(dy * bx - dx * by) / travel
        if lateral < 0.20:
            return goal
        if self.nav:
            origin = (*shooter[:2], shooter[2] + 7)
            if now >= self.check_cover_at:
                self.check_cover_at = now + 0.35
                self.open_ground = True
                for i in range(8):
                    angle = math.tau * i / 8
                    xy = (pos[0] + 19 * math.cos(angle), pos[1] + 19 * math.sin(angle))
                    if self.nav.walkable(*xy, radius) and not self.nav.line_clear(
                            origin, (*xy, self.nav.ground(*xy) + height * 0.75)):
                        self.open_ground = False
                        break
            if not self.open_ground:
                return goal
        if now >= self.reverse_at:
            self.weave_side *= -1
            self.reverse_at = now + self.rng.uniform(0.48, 1.12)
        if self.weave_side * (dy * bx - dx * by) >= 0:
            return goal
        ux = radial * bx - self.weave_side * lateral * by
        uy = radial * by + self.weave_side * lateral * bx
        reach = min(15, travel)
        end = pos[0] + ux * reach, pos[1] + uy * reach
        if dodge:
            # Both sides of a bullet's flight line can be safe. Predict how
            # far our legs can actually deflect before it crosses our path.
            _, normal, eta, offset = dodge
            me = obs["self"]
            stats = me.get("stats") or {}
            vx, vy = (me.get("vel") or (0, 0))[:2]
            speed = stats.get("boost_speed", 19.5) if self.boosting else stats.get("walk_speed", 11.7)
            accel = max(1.0, stats.get("ground_accel", 58.5))

            def miss(ax, ay):
                dvx, dvy = ax * speed - vx, ay * speed - vy
                ramp = max(0.001, math.hypot(dvx, dvy) / accel)
                factor = eta - ramp * 0.5 if eta >= ramp else 0.5 * eta * eta / ramp
                return abs(offset - (dvx * normal[0] + dvy * normal[1]) * factor)

            if miss(ux, uy) + 0.05 < min(radius + 0.5, miss(dx / travel, dy / travel)):
                return goal
        if self.nav:
            # Test the whole proposed maneuver at ground-grid resolution. A
            # narrow gap or a nearby landing must take precedence over a jink.
            for step in (0.25, 0.5, 0.75, 1.0):
                if not self.nav.walkable(pos[0] + ux * reach * step,
                                         pos[1] + uy * reach * step, radius):
                    return goal
            if not self.nav.line_clear(origin, (*goal[:2], self.nav.ground(*goal[:2]) + height * 0.75)):
                return goal
        return end

    def decide(self, obs):
        me, t = obs["self"], obs.get("t", 0)
        pos = me["pos"]
        stats = me.get("stats") or {}
        mech = self.rules.get("mech", {})
        speed = stats.get("walk_speed", mech.get("walk_speed", 11.7))
        radius = stats.get("radius", mech.get("radius", 2.5))
        hp = clip(me.get("hp", 1) / max(1, me.get("max_hp", 1)))
        energy = clip(me.get("energy", 100) / max(1, me.get("max_energy", 100)))
        anchor, urgency, circle, final, until = self._zone(obs, pos, speed, radius)
        foes, pressure, bearing = self._enemies(obs, t, pos)
        dodge = self._dodge(obs, pos, radius)
        goal, mode, target = anchor, "zone", None
        if urgency < 0.5 and pressure < (0.29 if hp < 0.65 else 0.45) and not dodge:
            loot = self._loot_goal(obs, t, pos, radius, hp, foes, circle, final, until)
            if loot:
                goal, mode, target = loot
            elif distance(pos, anchor) < 1 and (len(anchor) == 2 or pos[2] >= anchor[2] - 1.2):
                goal = self._shelter(t, pos, radius, stats.get("height", 9), final)
                mode = "hold" if distance(goal, pos) < 1 else "shelter"
        elif urgency < 0.85 and circle[1] > max(6, 1.6 * radius) and (dodge or pressure > (0.26 if hp < 0.72 else 0.40)):
            goal = self._evade(t, pos, radius, stats.get("height", 9), foes, bearing,
                               dodge, anchor, circle, urgency)
            mode = "evade"
        if mode != "evade":
            self.evade_until = -1
        if (self.pursuer and (not dodge or dodge[0] == "line")
                and mode in ("evade", "zone") and urgency < 0.3
                and me.get("grounded", True) and me.get("in_zone", True)
                and circle[1] - distance(pos, circle[0]) > 19 + radius and len(goal) == 2):
            goal = self._weave(obs, goal, radius, stats.get("height", 9), dodge)
        if mode not in ("hold", "shelter"):
            self.cover_until = -1
        # Hysteresis leaves energy for jumping obstacles, and lets regeneration
        # restart between escape bursts instead of toggling boost every frame.
        reserve = 0.10 if urgency >= 0.9 or dodge else 0.36
        stress = max(urgency, pressure, 1 if dodge else 0)
        self.boosting = (stress > 0.66 and distance(pos, goal) > 5
                         and energy > (reserve if self.boosting else reserve + 0.19))
        if (urgency < .35 and mode not in ("loot", "capture") and me.get("grounded", True)
                and not (dodge and dodge[0] == "blast")):
            goal = self._finish_goal(obs, foes, circle, radius, hp, goal)
        return {"goal": goal, "mode": mode, "urgency": max(urgency, pressure),
                "boost": self.boosting, "threat_yaw": bearing, "target_id": target}
