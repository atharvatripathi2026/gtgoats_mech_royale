"""Campus ground routing and shot-cover queries on a three-metre grid."""

from array import array
from collections import deque
from heapq import heappop, heappush
import json
import math
from pathlib import Path
import sys


CELL = 3.0
DIAGONAL = math.sqrt(2.0)


def _direction(dx, dy):
    norm = math.hypot(dx, dy)
    if norm < 0.12:
        return 0.0, 0.0
    return dx / norm, dy / norm


class Navigator:
    def __init__(self, map_dir, config=None):
        mech = (config or {}).get("mech", {})
        self.body_height = float(mech.get("height", 9.0))
        self.body_radius = float(mech.get("radius", 2.5))
        self.step_up = float(mech.get("step_up", 1.2))
        self.slope = math.tan(math.radians(mech.get("max_slope_deg", 50)))
        self.loaded = False
        self.path = []
        self.path_goal = None
        self.flow_key = None
        self.flow = None
        self.plan_tick = -100
        self.anchor = None
        self.escape_end = -1
        self.escape_sign = 1
        self.roof_approaches = {}
        self.ascent_target = None
        try:
            self._load(Path(map_dir) / "v2")
        except (OSError, ValueError, TypeError, KeyError, IndexError, OverflowError) as exc:
            print(f"Map unavailable: {exc}", file=sys.stderr, flush=True)

    def _load(self, folder):
        with (folder / "world.json").open() as stream:
            world = json.load(stream)
        terrain = world["terrain"]
        self.tx, self.ty = terrain["minX"], terrain["minY"]
        self.tw, self.th = terrain["nx"], terrain["ny"]
        self.ts = terrain["step"]
        self.scale = terrain.get("scale", 0.01)
        self.samples = array("h")
        with (folder / "terrain.i16").open("rb") as stream:
            self.samples.frombytes(stream.read())
        if len(self.samples) != self.tw * self.th or min(self.tw, self.th) < 2:
            raise ValueError("invalid terrain dimensions")
        if sys.byteorder != "little":
            self.samples.byteswap()
        b = world["bounds"]
        self.ox, self.oy = b["minX"] + CELL / 2, b["minY"] + CELL / 2
        self.w = math.ceil((b["maxX"] - b["minX"]) / CELL)
        self.h = math.ceil((b["maxY"] - b["minY"]) / CELL)
        n = self.w * self.h
        self.floors = array("f", (self._terrain(self.ox + i * CELL, self.oy + j * CELL)
                                   for j in range(self.h) for i in range(self.w)))
        self.solids = [()] * n
        for prism in world.get("prisms", []):
            self._rasterize(prism)
        # Every cell keeps all vertical intervals, including gaps below bridges.
        self.clearance = bytearray([250]) * n
        self.headroom = array("f", [1e6]) * n
        for i, intervals in enumerate(self.solids):
            floor = self.floors[i]
            for lo, hi in intervals:
                if hi > floor + self.step_up:
                    self.headroom[i] = min(self.headroom[i], max(0.0, lo - floor))
            if (self.headroom[i] < self.body_height or i % self.w in (0, self.w - 1)
                    or i < self.w or i >= n - self.w):
                self.clearance[i] = 0
        # Chamfer distance from each ground cell to the nearest obstruction.
        c, w = self.clearance, self.w
        for i in range(w + 1, n - w - 1):
            if c[i]:
                c[i] = min(c[i], c[i-1]+3, c[i-w]+3, c[i-w-1]+4, c[i-w+1]+4)
        for i in range(n-w-2, w, -1):
            if c[i]:
                c[i] = min(c[i], c[i+1]+3, c[i+w]+3, c[i+w-1]+4, c[i+w+1]+4)
        self._index_roofs()
        self.loaded = True

    def _index_roofs(self):
        # Each entry pairs a clear ground launch column with a landing point
        # one grid cell behind the lip. Keep distinct approaches to a roof.
        self.roof_buckets = {}
        w = self.w
        top = array("f", (max((hi for _, hi in spans), default=floor)
                          for spans, floor in zip(self.solids, self.floors)))
        self.roof_heights = top
        for i, spans in enumerate(self.solids):
            if not spans or not 5.0 <= top[i] - self.floors[i] <= 45:
                continue
            y, x = divmod(i, w)
            if not (3 <= x < w-3 and 3 <= y < self.h-3):
                continue
            for step in (-1, 1, -w, w):
                if (y if abs(step) == 1 else x) % 2:
                    continue
                side, launch, landing = i+step, i+2*step, i-step
                if (self.solids[side] or self.solids[launch] or self.clearance[launch] < 4
                        or abs(top[landing]-top[i]) > self.step_up
                        or not self.solids[landing]):
                    continue
                px, py = self._xy(landing)
                ax, ay = self._xy(launch)
                entry = (px, py, float(top[landing]), ax, ay)
                self.roof_buckets.setdefault((x//8, y//8), []).append(entry)

    def roof_candidates(self, pos, radius, max_distance=42, threat=None):
        """Nearby reachable roof landings with unobstructed ground approaches."""
        if not self.loaded:
            return []
        x, y, z = pos
        ix, iy = self._ij(x, y)
        reach = math.ceil(min(80, max_distance) / CELL) + 4
        clearance, height = self._dimensions(radius)
        ranked = []
        for by in range((iy-reach)//8, (iy+reach)//8+1):
            for bx in range((ix-reach)//8, (ix+reach)//8+1):
                for px, py, roof, ax, ay in self.roof_buckets.get((bx, by), ()):
                    rise = roof-z
                    travel = math.hypot(ax-x, ay-y)
                    if not (5 <= rise <= 42 and travel <= max_distance
                            and math.hypot(px-x, py-y) <= max_distance):
                        continue
                    score = travel + 0.32*abs(rise-19)
                    if threat is not None:
                        # Approach behind the roof relative to a pursuer.
                        score += 0.38*(math.hypot(px-threat[0],py-threat[1])
                                       - math.hypot(ax-threat[0],ay-threat[1]))
                    ranked.append((score, (px,py,roof), (ax,ay)))
        result = []
        for _, point, approach in sorted(ranked)[:40]:
            px, py, roof = point
            if any(math.hypot(px-p[0],py-p[1]) < 10 for p in result):
                continue
            if (self._landing_height(px,py,roof,radius,height) > roof + self.step_up
                    or not self._ground_segment(x,y,*approach,clearance,height)):
                continue
            self.roof_approaches[point] = approach
            result.append(point)
            if len(result) == 6:
                break
        return result

    def same_roof(self, start, end, radius):
        if not self.loaded or len(start) < 3 or len(end) < 3:
            return False
        x, y, feet = start
        dx, dy = end[0]-x, end[1]-y
        length = math.hypot(dx, dy)
        if length > 60 or feet < self.ground(x,y)+4:
            return False
        _, height = self._dimensions(radius)
        n = max(1, math.ceil(length/(CELL*0.65)))
        for step in range(n+1):
            px, py = x+dx*step/n, y+dy*step/n
            i = self._index(px, py)
            level = self.roof_heights[i]
            if (not self.solids[i] or abs(level-feet) > self.step_up+0.05
                    or self._landing_height(px,py,level,radius,height) > level+self.step_up):
                return False
            feet = level
        return abs(feet-end[2]) <= self.step_up+0.05

    def roof_perch(self, pos, radius, threat, max_distance=32):
        """Find a same-roof point with a clear shot and a continuous walk to it."""
        if not self.loaded or threat is None:
            return None
        x, y, z = pos
        if z < self.ground(x,y)+4 or abs(self.surface(x,y)-z) > 1.5:
            return None
        _, height = self._dimensions(radius)
        target_z = threat[2] if len(threat) >= 3 else self.ground(*threat[:2])
        target = (threat[0], threat[1], target_z+4.5)
        def firing_point(px, py, pz):
            dx = math.hypot(px-target[0], py-target[1])
            muzzle = pz+height*7/9
            return (target[2]-muzzle >= -0.84*dx and
                    self.line_clear((px,py,muzzle),target))
        if firing_point(x,y,z):
            return (x,y,z)
        yaw = math.atan2(threat[1]-y,threat[0]-x)
        options = []
        for offset in (0.0, 0.52, -0.52, 1.05, -1.05, 1.57, -1.57, 2.09, -2.09):
            ux, uy = math.cos(yaw+offset), math.sin(yaw+offset)
            previous = z
            for step in range(1, int(min(48,max_distance)/CELL)+1):
                d = step*CELL
                px, py = x+d*ux, y+d*uy
                i = self._index(px,py)
                level = self.roof_heights[i]
                if (not self.solids[i] or abs(level-previous) > self.step_up
                        or self._landing_height(px,py,level,radius,height) > level+self.step_up):
                    break
                if firing_point(px,py,level):
                    options.append((d+abs(offset), (px,py,level)))
                    break
                previous = level
        return min(options)[1] if options else None

    def _rasterize(self, prism):
        edges = []
        for flat in (prism["ring"], *prism.get("holes", [])):
            points = list(zip(flat[::2], flat[1::2]))
            for (x1, y1), (x2, y2) in zip(points, points[1:] + points[:1]):
                if y2 != y1:
                    edges.append((min(y1, y2), max(y1, y2), x1, y1, (x2-x1)/(y2-y1)))
        if not edges:
            return
        first = max(0, math.ceil((min(e[0] for e in edges) - self.oy) / CELL))
        last = min(self.h, math.ceil((max(e[1] for e in edges) - self.oy) / CELL))
        span = ((float(prism["base"]), float(prism["top"])),)
        for j in range(first, last):
            y = self.oy + j * CELL
            xs = sorted(x + (y - y1) * k for ymin, ymax, x, y1, k in edges if ymin <= y < ymax)
            for left, right in zip(xs[::2], xs[1::2]):
                a = max(0, math.ceil((left - self.ox) / CELL))
                b = min(self.w, math.ceil((right - self.ox) / CELL))
                for i in range(j*self.w+a, j*self.w+b):
                    self.solids[i] += span

    def _terrain(self, x, y):
        x = min(self.tw - 1, max(0.0, (x - self.tx) / self.ts))
        y = min(self.th - 1, max(0.0, (y - self.ty) / self.ts))
        i, j = min(int(x), self.tw - 2), min(int(y), self.th - 2)
        fx, fy = x - i, y - j
        k, s = j*self.tw+i, self.samples
        bottom = s[k] + fx*(s[k+1]-s[k])
        top = s[k+self.tw] + fx*(s[k+self.tw+1]-s[k+self.tw])
        return (bottom + fy*(top-bottom))*self.scale

    def ground(self, x, y):
        return self._terrain(x, y) if self.loaded else 0.0

    def _ij(self, x, y):
        return (min(self.w-1, max(0, math.floor((x-self.ox)/CELL+0.5))),
                min(self.h-1, max(0, math.floor((y-self.oy)/CELL+0.5))))

    def _index(self, x, y):
        i, j = self._ij(x, y)
        return j * self.w + i

    def _xy(self, index):
        j, i = divmod(index, self.w)
        return self.ox + i*CELL, self.oy + j*CELL

    def surface(self, x, y):
        if not self.loaded:
            return 0.0
        floor = self.ground(x, y)
        for _, top in self.solids[self._index(x, y)]:
            floor = max(floor, top)
        return floor

    def _landing_height(self, x, y, feet, radius, height):
        # The center of a closing circle can be beside a wall while the
        # mech's cylinder still overlaps it. Clear that eave before landing.
        ix, iy = self._ij(x, y)
        reach = math.ceil(radius / CELL + 0.5)
        landing = feet
        for j in range(max(0, iy-reach), min(self.h, iy+reach+1)):
            for i in range(max(0, ix-reach), min(self.w, ix+reach+1)):
                dx = max(0.0, abs(self.ox+i*CELL-x) - CELL/2)
                dy = max(0.0, abs(self.oy+j*CELL-y) - CELL/2)
                if dx*dx+dy*dy <= radius*radius:
                    for low, top in self.solids[j*self.w+i]:
                        if low < feet+height:
                            landing = max(landing, top)
        return landing

    def _dimensions(self, radius):
        return math.ceil((radius+1.05)*3/CELL), self.body_height * radius/self.body_radius

    def walkable(self, x, y, radius=2.5):
        if not self.loaded:
            return True
        i = self._index(x, y)
        clearance, height = self._dimensions(radius)
        return self.clearance[i] >= clearance and self.headroom[i] >= height

    def line_clear(self, start, end):
        """Approximate projectile visibility; callers provide both endpoint heights."""
        if not self.loaded:
            return True
        x, y, z = start[:3]
        dx, dy, dz = end[0]-x, end[1]-y, end[2]-z
        steps = max(1, math.ceil(max(abs(dx), abs(dy)) / (CELL*0.65)))
        dx, dy, dz = dx/steps, dy/steps, dz/steps
        gx, gy = (x-self.ox)/CELL+0.5, (y-self.oy)/CELL+0.5
        gx, gy, z = gx+dx/(2*CELL), gy+dy/(2*CELL), z+dz/2
        sx, sy = dx/CELL, dy/CELL
        for _ in range(steps):
            if not (0 <= gx < self.w and 0 <= gy < self.h):
                return False
            i = int(gy)*self.w+int(gx)
            if self.floors[i] > z + 0.12:
                return False
            for low, high in self.solids[i]:
                if low <= z <= high:
                    return False
            gx, gy, z = gx+sx, gy+sy, z+dz
        return True

    def _snap(self, cell, clearance, height):
        if self.clearance[cell] >= clearance and self.headroom[cell] >= height:
            return cell
        y, x = divmod(cell, self.w)
        # A target such as the zone center can be inside the stadium.
        for r in range(1, 45):
            best, best_d = None, 2*r*r+1
            for j in range(max(1, y-r), min(self.h-1, y+r+1)):
                xl, xr = max(1, x-r), min(self.w-2, x+r)
                columns = range(xl, xr+1) if abs(j-y) == r else (xl, xr)
                for k in columns:
                    i = j*self.w+k
                    d = (x-k)**2 + (y-j)**2
                    if d < best_d and self.clearance[i] >= clearance and self.headroom[i] >= height:
                        best, best_d = i, d
            if best is not None:
                return best
        return None

    def _ground_segment(self, x, y, ex, ey, clearance, height):
        dx, dy = ex-x, ey-y
        n = max(1, math.ceil(max(abs(dx), abs(dy)) / (CELL*0.57)))
        dx, dy = dx/n, dy/n
        previous = self._index(x, y)
        for _ in range(n):
            x, y = x+dx, y+dy
            i = self._index(x, y)
            if self.clearance[i] < clearance or self.headroom[i] < height:
                return False
            gap = abs(i-previous)
            if gap:
                planar = CELL * (DIAGONAL if gap not in (1, self.w) else 1)
                if self.floors[i] - self.floors[previous] > self.slope * planar:
                    return False
            previous = i
        return True

    def _plan(self, start, goal, clearance, height):
        start = self._snap(start, clearance, height)
        goal = self._snap(goal, clearance, height)
        if start is None or goal is None:
            return []
        w = self.w
        gy, gx = divmod(goal, w)
        cost = {start: 0.0}
        parent = {}
        q = [(0.0, 0.0, start)]
        best, closest = start, float("inf")
        c, head, floors = self.clearance, self.headroom, self.floors
        directions = ((1,1,0),(-1,-1,0),(w,0,w),(-w,0,-w),
                      (w+1,1,w),(w-1,-1,w),(1-w,1,-w),(-w-1,-1,-w))
        # The nearest frontier gives a usable partial path when the search budget expires.
        for _ in range(950):
            if not q:
                break
            _, g, i = heappop(q)
            if g != cost[i]:
                continue
            y, x = divmod(i, w)
            dx, dy = abs(x-gx), abs(y-gy)
            dist = max(dx, dy) + (DIAGONAL-1)*min(dx, dy)
            if dist < closest:
                best, closest = i, dist
            if i == goal:
                break
            for delta, hx, vy in directions:
                j = i+delta
                diag = hx != 0 and vy != 0
                if c[j] < clearance or head[j] < height:
                    continue
                if diag and (c[i+hx] < clearance or c[i+vy] < clearance
                             or head[i+hx] < height or head[i+vy] < height):
                    continue
                length = DIAGONAL if diag else 1.0
                if floors[j] - floors[i] > self.slope * CELL * length:
                    continue
                travel = g+length+(0.10 if c[j] < clearance+3 else 0.0)
                if travel >= cost.get(j, float("inf")):
                    continue
                jy, jx = divmod(j, w)
                dx, dy = abs(jx-gx), abs(jy-gy)
                h = max(dx, dy) + (DIAGONAL-1)*min(dx, dy)
                cost[j], parent[j] = travel, i
                heappush(q, (travel+1.42*h, travel, j))
        result = [best]
        while result[-1] != start:
            result.append(parent[result[-1]])
        # Store in reverse so that reached points can be popped from the tail.
        return result

    def _flow_path(self, cell, target, clearance, height):
        # A changing goal gets an immediate bounded A* route. A persistent goal
        # also gets a reverse flood, spread over observations, so a large stadium
        # detour cannot trap the bot behind a locally unpromising first step.
        key = (target, clearance, height)
        if key != self.flow_key:
            self.flow_key = key
            end = self._snap(target, clearance, height)
            self.flow = bytearray(len(self.clearance))
            self.frontier = deque()
            if end is not None:
                self.flow[end] = 5
                self.frontier.append(end)
        w, flow = self.w, self.flow
        if not flow[cell]:
            for _ in range(1000):
                if not self.frontier:
                    break
                i = self.frontier.popleft()
                for back, j in ((2,i-1), (1,i+1), (4,i-w), (3,i+w)):
                    if (not flow[j] and self.clearance[j] >= clearance and self.headroom[j] >= height
                            and self.floors[i] - self.floors[j] <= self.slope * CELL):
                        flow[j] = back
                        self.frontier.append(j)
                if flow[cell]:
                    break
        if not flow[cell]:
            return None
        steps = (0, -1, 1, -w, w)
        result = [cell]
        for _ in range(12):
            direction = flow[result[-1]]
            if direction == 5:
                break
            result.append(result[-1] + steps[direction])
        result.reverse()
        return result

    def _stuck(self, x, y, tick):
        if self.anchor is None or tick < self.anchor[2]:
            self.anchor = (x, y, tick)
        elif tick - self.anchor[2] >= 26:
            px, py, _ = self.anchor
            self.anchor = (x, y, tick)
            if math.hypot(x-px, y-py) < 1.4:
                self.escape_end = tick+17
                self.escape_sign *= -1
                self.path.clear()
        return tick < self.escape_end

    def steer(self, pos, goal, tick, *, radius=2.5):
        x, y = pos[:2]
        gx, gy = goal[:2]
        dx, dy = gx-x, gy-y
        key = tuple(goal)
        if self.ascent_target != key:
            self.ascent_target = None
        launch = self.roof_approaches.get(key)
        if launch is not None and len(pos) >= 3:
            z = pos[2]
            below_lip = self.surface(x, y) < goal[2]-self.step_up
            if self.ascent_target == key:
                # Keep the cylinder in the open launch column while it rises.
                # Moving into an overhang early can pin the jet under an eave.
                if z < goal[2]-4:
                    lx, ly = launch[0]-x, launch[1]-y
                    scale = max(3.5, math.hypot(lx,ly))
                    return lx/scale, ly/scale, True
                ux, uy = _direction(dx, dy)
                jet = z < goal[2]+0.6 if below_lip else z < goal[2]-self.step_up
                return ux, uy, jet
            if z < goal[2]-self.step_up:
                if math.hypot(x-launch[0], y-launch[1]) < 3.0:
                    self.ascent_target = key
                    return 0.0, 0.0, True
                # Follow the ground route to this roof's vetted launch side.
                gx, gy = goal = launch
                dx, dy = gx-x, gy-y
        direct_x, direct_y = _direction(dx, dy)
        dist = math.hypot(dx, dy)
        if dist < 0.45 and (len(goal) < 3 or len(pos) < 3 or goal[2]-pos[2] < 2):
            self.anchor = None
            return 0.0, 0.0, False
        stuck = self._stuck(x, y, tick)
        if not self.loaded:
            return direct_x, direct_y, stuck

        clearance, height = self._dimensions(radius)
        z = pos[2] if len(pos) > 2 else self.ground(x, y)
        landing = goal[2] if len(goal) >= 3 else None
        if landing is not None and dist <= max(13.0, radius*3.5):
            landing = self._landing_height(gx, gy, landing, radius, height)
        climb = landing is not None and landing > z + self.step_up
        if climb and dist <= max(13.0, radius*3.5):
            return direct_x, direct_y, True
        if z > self.ground(x, y) + 2.2:
            # Walk along a roof or keep horizontal momentum while descending.
            # Test a short cylinder-height slice ahead at the current altitude.
            look = min(9.0, dist)
            base = (x, y, z+self.step_up+0.3)
            for angle in (0, 0.60, -0.60, 1.08, -1.08, 1.55, -1.55):
                a = angle*self.escape_sign
                ca, sa = math.cos(a), math.sin(a)
                ux, uy = ca*direct_x-sa*direct_y, sa*direct_x+ca*direct_y
                end = (x+look*ux, y+look*uy, base[2])
                if self.line_clear(base, end):
                    return ux, uy, stuck
            return direct_x, direct_y, True

        if self._ground_segment(x,y,gx,gy,clearance,height):
            self.path.clear()
            if stuck:
                # Fine geometry or another mech may block a coarse-grid path.
                side = self.escape_sign
                return 0.6*direct_x-0.8*side*direct_y, 0.6*direct_y+0.8*side*direct_x, True
            return direct_x, direct_y, False

        cell, target = self._index(x, y), self._index(gx, gy)
        goal_changed = self.path_goal is None or math.hypot(gx-self.path_goal[0],gy-self.path_goal[1]) > 9
        flow_path = self._flow_path(cell, target, clearance, height)
        if flow_path is not None and (not self.path or goal_changed or tick - self.plan_tick >= 10):
            self.path = flow_path
            self.path_goal = (gx, gy)
            self.plan_tick = tick
        elif (not self.path or goal_changed) and tick - self.plan_tick >= 6:
            self.path = self._plan(cell, target, clearance, height)
            self.path_goal = (gx, gy)
            self.plan_tick = tick
        while self.path:
            px, py = self._xy(self.path[-1])
            if math.hypot(px-x, py-y) > 1.6:
                break
            self.path.pop()
        if self.path:
            # Smooth only a short prefix; a long diagonal can cut a corner.
            for skip in range(min(6, len(self.path)-1), 0, -1):
                px, py = self._xy(self.path[-1-skip])
                if self._ground_segment(x,y,px,py,clearance,height):
                    del self.path[-skip:]
                    break
            px, py = self._xy(self.path[-1])
            ux, uy = _direction(px-x, py-y)
            return ux, uy, stuck
        if climb and dist <= 30 and not self.walkable(gx, gy, radius):
            return direct_x, direct_y, True
        if len(goal) >= 3 and self.clearance[target] < clearance and dist < 8:
            return direct_x, direct_y, True
        if self.clearance[target] < clearance and dist < 8 and not climb:
            self.anchor = None
            return 0.0, 0.0, False
        return direct_x, direct_y, stuck
