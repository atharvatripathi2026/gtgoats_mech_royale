"""Deterministic, action-reactive Mech Royale training episodes.

One player faces three scripted rivals. Every participant has a position, HP,
weapons and zone exposure throughout the episode. The score is 4 minus the
player's local place. Deaths in one integration step tie; the timeout ranks
survivors by HP. These four-mech results are a surrogate for tournament play.

The kit supplies the recorded hello and balance config. By default each seed
generates a compact flat training map with rectangular buildings. campus=True
uses the kit's campus terrain and rasterized solids. Collision, ballistic hits,
sensing, recoil, NPCs and opponent behavior are approximations. The training
episode has an accelerated circle, no supply drops, and simplified upgrades.
"""
import copy
import gzip
import json
import math
import random
import tempfile
import time
from pathlib import Path

from navigation import Navigator

SCENARIOS = ("forage", "pursuit", "crossfire", "rotation")
# Seconds before each rival actively pursues, plus episode duration.
SCHEDULE = {
    "forage": ((15, 30, 41), 54),
    "pursuit": ((1, 19, 31), 45),
    "crossfire": ((1, 4, 25), 39),
    "rotation": ((6, 17, 30), 48),
}


def clamp(value, lower, upper):
    return max(lower, min(value, upper))


def wrap(angle):
    return (angle + math.pi) % math.tau - math.pi


def horizontal(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


class Layout:
    """Same map data for the player and the local integration step."""
    def __init__(self, directory, boxes=None, config=None, limit=289.):
        self.directory = directory
        self.boxes = boxes
        self.limit = limit
        self.nav = Navigator(directory, config) if boxes is None else None
        if self.nav and not self.nav.loaded:
            raise ValueError(f"Unable to load campus map at {directory}")

    def ground(self, x, y):
        return self.nav.ground(x, y) if self.nav else 0.

    def surface(self, x, y):
        if self.nav:
            return self.nav.surface(x, y)
        return max((h for l, b, r, t, h in self.boxes if l < x < r and b < y < t), default=0.)

    def walk(self, x, y, feet, radius):
        if self.nav:
            top = self.nav.surface(x, y)
            return self.nav.walkable(x, y, radius) or top <= feet + 1.2
        if max(abs(x), abs(y)) + radius > self.limit:
            return False
        return all(feet + 1.2 >= h or x <= l-radius or x >= r+radius or
                   y <= b-radius or y >= t+radius for l, b, r, t, h in self.boxes)

    def clear(self, a, b):
        if self.nav:
            return self.nav.line_clear(a, b)
        # Segment/box intersection, including the roof and ground.
        for l, bottom, r, top, height in self.boxes:
            enter, leave = 0., 1.
            for start, stop, lo, hi in zip(a, b, (l, bottom, -5.), (r, top, height)):
                step = stop - start
                if abs(step) < 1e-8:
                    if start < lo or start > hi:
                        leave = -1.
                        break
                else:
                    near, far = (lo-start)/step, (hi-start)/step
                    enter, leave = max(enter, min(near, far)), min(leave, max(near, far))
            if enter <= leave:
                return False
        return True


class Arena:
    def __init__(self, kit_dir, *, campus=False):
        kit = Path(kit_dir).expanduser().resolve()
        with gzip.open(kit / "check" / "stream.jsonl.gz", "rt") as stream:
            self.hello = json.loads(next(stream))
        if self.hello.get("protocol") != "mechfight/1":
            raise ValueError("Expected a mechfight/1 kit")
        self.scratch = tempfile.TemporaryDirectory(prefix="astra-training-")
        self.layouts = {}
        self.campus = Layout(kit / "arena", config=self.hello["config"]) if campus else None

    def close(self):
        self.scratch.cleanup()

    def _layout(self, seed, scenario):
        if self.campus:
            return self.campus
        # Disjoint seeds produce disjoint training and evaluation layouts.
        key = (scenario, seed)
        if key in self.layouts:
            return self.layouts[key]
        rng = random.Random(f"map/{key}")
        directory = Path(self.scratch.name) / f"{scenario}-{key[1]}"
        v2 = directory / "v2"
        v2.mkdir(parents=True)
        boxes, prisms = [], []
        count = {"forage": 2, "pursuit": 3, "crossfire": 4, "rotation": 3}[scenario]
        offset = rng.uniform(-math.pi, math.pi)
        for i in range(count):
            yaw = offset + i * math.tau / count
            d = rng.uniform(30, 73)
            x, y = d * math.cos(yaw), d * math.sin(yaw)
            hw, hh = rng.uniform(4.5, 12), rng.uniform(7, 17)
            l, r, b, t = x - hw, x + hw, y - hh, y + hh
            h = rng.uniform(10, 24)
            boxes.append((l, b, r, t, h))
            prisms.append(dict(kind="building", base=0, top=h, ring=[l,b,r,b,r,t,l,t], holes=[]))
        edge = 290 if scenario in ("forage","pursuit") else 145
        # Training surfaces are flat; a coarser heightfield represents them exactly.
        terrain = dict(minX=-edge, minY=-edge, step=2, nx=edge+1, ny=edge+1, scale=.01, file="terrain.i16")
        world = dict(bounds=dict(minX=-edge, maxX=edge, minY=-edge, maxY=edge), terrain=terrain,
                     prisms=prisms, trees=dict(fields=[], data=[]))
        (v2/"world.json").write_text(json.dumps(world), encoding="utf-8")
        (v2/"terrain.i16").write_bytes(bytes(2 * (edge+1)**2))
        self.layouts[key] = Layout(directory, boxes, limit=edge-1)
        return self.layouts[key]

    def run(self, bot_factory, seed, scenario="pursuit", *, trace=None):
        """trace(obs, applied_action, outcome) receives detached per-decision data."""
        if scenario not in SCENARIOS:
            raise ValueError(f"Unknown scenario {scenario!r}")
        layout = self._layout(int(seed), scenario)
        hello = copy.deepcopy(self.hello)
        hello["config"]["match"]["mechs"] = 4
        # A slot seed remains fixed as the environment seed changes.
        hello.update(slot=0,
                     map={"dir": str(layout.directory), "files": ["v2/world.json", "v2/terrain.i16"]})
        return Episode(hello, layout, int(seed), scenario).run(bot_factory(copy.deepcopy(hello)), trace)


class Actor:
    def __init__(self, ident, kind, pos, config, seed):
        self.id, self.kind = ident, kind
        section = config["crates" if kind == "crate" else kind]
        self.radius, self.height = section["radius"], section["height"]
        self.hp = self.max_hp = float(section["hp"])
        self.pos, self.home = list(pos), tuple(pos)
        self.vel = [0., 0., 0.]
        self.rng = random.Random(f"actor/{seed}/{ident}")
        self.aim = [self.rng.uniform(-math.pi, math.pi), 0.]
        self.stats = dict(config["mech"])
        self.grounded = True
        self.energy = self.stats["energy"]
        self.cubes = 0
        self.upgrades = []
        self.weapons = [None, None]
        self.last_cost = self.last_damage = -100.
        self.events, self.sounds = [], []
        self.hunting = False
        self.zone_ok = True
        self.offer = None
        self.npc_ready = 0.

    def equip(self, slot, kind, cfg, delay=0.):
        stats = dict(cfg["weapons"][kind])
        w = dict(kind=kind, stats=stats, cooldown=delay)
        if kind == "gun":
            w.update(ammo=stats["mag"], reload=0.)
        if kind == "laser":
            w["charge"] = 0.
        self.weapons[slot] = w

    def state(self):
        return dict(id=self.id, pos=self.pos, vel=self.vel, aim=self.aim, hp=self.hp,
                    max_hp=self.max_hp, energy=self.energy, max_energy=self.stats["energy"],
                    grounded=self.grounded, cubes=self.cubes, in_zone=self.zone_ok,
                    upgrades=self.upgrades, stats=self.stats, weapons=self.weapons)


class Episode:
    def __init__(self, hello, layout, seed, scenario):
        self.opponents=(1,2,3)
        self.cfg, self.layout, self.seed, self.scenario = hello["config"], layout, seed, scenario
        self.rng = random.Random(f"episode/{seed}/{scenario}")
        self.dt = 1 / self.cfg["match"]["tick_hz"]
        self.stride = self.cfg["match"]["decide_every"]
        self.now = 0.
        self.schedule, self.duration = SCHEDULE[scenario]
        self.idle_until = [d + self.rng.uniform(-1, 1) for d in self.schedule]
        self.actors = {}
        self.shots, self.pickups, self.cubes = [], [], []
        self.dead, self.memory = {}, {}
        self.next_id = 10000
        self.dealt = self.taken = self.zone_damage = 0.
        self.kills = 0
        self.center = (self.rng.uniform(-30, 30), self.rng.uniform(-25, 25)) if layout.nav else (0., 0.)
        self.next_center = self.point(self.center, 42, 76)[:2]
        self.opening = scenario in ("forage", "pursuit")
        self.radius = self.cfg["zone"]["start_radius"] if self.opening else 145.
        self.zone = {}
        self.player = self.spawn(0, "mech", self.center, 0, 35)
        if scenario == "rotation":
            self.player.pos = self.point(self.next_center, 90, 114)
        for i in range(1, 4):
            # Early-game matches have one nearby hunter. Rivals farther than
            # sensor range remain physically present and must travel to engage.
            if self.opening and i > 1:
                near, far = 219, 258
            else:
                near, far = 65, 124
            enemy = self.spawn(i, "mech", self.player.pos, near, far)
            enemy.aim[0] = self.bearing(enemy, self.player)
            if i == 1 and scenario == "pursuit":
                # This scenario begins at first contact, as opposed to a loot spawn.
                self.player.aim[0] = self.bearing(self.player, enemy) + self.rng.uniform(-.4,.4)
            if i == 3:
                enemy.equip(1, self.rng.choice(("laser", "lightning", "mortar")), self.cfg)
        for i in range(3 if scenario == "forage" else 2):
            self.spawn(1000+i, "crate", self.player.pos, 15, 75)
        self.spawn(100, "npc", self.player.pos, 32, 85)
        for i in range(3):
            self.pickups.append(dict(id=8000+i, kind=self.rng.choice(("laser","lightning","mortar")),
                                     pos=self.point(self.player.pos, 9, 94)))

    def point(self, origin, near, far):
        for _ in range(200):
            angle, d = self.rng.uniform(-math.pi, math.pi), self.rng.uniform(near, far)
            x, y = origin[0]+d*math.cos(angle), origin[1]+d*math.sin(angle)
            if max(abs(x), abs(y)) > self.layout.limit - 8:
                continue
            z = self.layout.ground(x, y)
            if self.layout.walk(x, y, z, 3.) and all(horizontal((x,y), a.pos) > 7 for a in self.actors.values()):
                return [x, y, z]
        raise RuntimeError("No open local spawn point; try another scenario seed")

    def spawn(self, ident, kind, origin, near, far):
        actor = Actor(ident, kind, self.point(origin, near, far), self.cfg, self.seed)
        self.actors[ident] = actor
        if kind == "mech":
            actor.equip(0, "gun", self.cfg)
        return actor

    @staticmethod
    def bearing(a, b):
        return math.atan2(b.pos[1]-a.pos[1], b.pos[0]-a.pos[0])

    def update_zone(self):
        if self.opening:
            phase = self.cfg["zone"]["phases"][0]
            start, finish = phase["hold_s"], phase["hold_s"] + phase["shrink_s"]
            radius, dps = phase["radius"], phase["dps"]
        else:
            start = 5 if self.scenario == "rotation" else self.duration * .36
            finish = self.duration
            radius = 13 if self.scenario == "rotation" else 33
            dps = 90 if self.scenario == "rotation" else 45
        u = clamp((self.now-start)/(finish-start), 0., 1.)
        center = [a+(b-a)*u for a,b in zip(self.center,self.next_center)]
        self.zone = dict(center=center, radius=self.radius+(radius-self.radius)*u,
                         next_center=self.next_center, next_radius=radius, shrink_start=start,
                         shrink_end=finish, dps=dps)

    def visible(self, viewer, p, height=0.):
        v = self.cfg["vision"]
        d = horizontal(p, viewer.pos)
        yaw = math.atan2(p[1]-viewer.pos[1],p[0]-viewer.pos[0])
        if d > v["range"] or (d > v["near_range"] and abs(wrap(yaw-viewer.aim[0])) > math.radians(v["fov_deg"]*.5)):
            return False
        eye = (*viewer.pos[:2],viewer.pos[2]+viewer.stats["eye_height"])
        return self.layout.clear(eye, (*p[:2],p[2]+max(.25,height*.5)))

    def obs(self, tick):
        me = self.player
        targets, crates = [], []
        for ident, a in self.actors.items():
            if a is me or a.hp <= 0:
                continue
            visible = self.visible(me, a.pos, a.height)
            if a.kind == "crate":
                if visible:
                    crates.append(dict(id=ident, pos=a.pos, hp=a.hp))
                continue
            if visible:
                self.memory[ident] = self.now
            if self.now-self.memory.get(ident,-100.) <= self.cfg["vision"].get("memory_s",5):
                targets.append(dict(id=ident, kind=a.kind, pos=a.pos, vel=a.vel, aim=a.aim,
                                    hp=a.hp, max_hp=a.max_hp, cubes=a.cubes,
                                    weapons=[w["kind"] for w in a.weapons if w],
                                    charging=any(w and w.get("charge",0)>0 for w in a.weapons)))
        shots = [dict(id=s["id"],kind=s["kind"],pos=s["pos"],vel=s["vel"]) for s in self.shots
                 if s["owner"] != me.id and self.visible(me,s["pos"])]
        obs = dict(type="obs",tick=tick,t=self.now,alive=1+len(self.opponents)-len(self.dead),self=me.state(),
                   mechs=targets, projectiles=shots, crates=crates, drops=[], beams=[],
                   pickups=[p for p in self.pickups if self.visible(me,p["pos"])],
                   cubes=[c for c in self.cubes if self.visible(me,c["pos"])],
                   events=me.events, sounds=me.sounds, offer=me.offer, zone=self.zone)
        me.events, me.sounds = [], []
        return copy.deepcopy(obs)

    def house(self, a):
        me = self.player
        d = max(1.,horizontal(a.pos,me.pos))
        heading = self.bearing(a,me)
        active = self.now >= self.idle_until[a.id-1] or a.hunting
        inside = horizontal(a.pos,self.zone["center"]) < self.zone["radius"]-5
        if active and inside:
            angle = heading + (1 if a.id%2 else -1) * (.20 if d>80 else .73 if d>34 else 1.45)
        else:
            point = self.zone["next_center"] if not inside else a.home
            angle = math.atan2(point[1]-a.pos[1], point[0]-a.pos[0]) + .3*math.sin(.2*self.now+a.id)
        speed = 1. if active or not inside else .15
        # Obstacles affect both teams. Level-ground rivals skirt solid walls.
        for offset in (0., .7, -.7, 1.5, -1.5, math.pi):
            dx,dy = math.cos(angle+offset),math.sin(angle+offset)
            if self.layout.walk(a.pos[0]+5*dx,a.pos[1]+5*dy,a.pos[2],a.radius):
                break
        lead = (.14 + .24*a.id) * d / self.cfg["weapons"]["gun"]["speed"]
        ex,ey = me.pos[0]+me.vel[0]*lead-a.pos[0], me.pos[1]+me.vel[1]*lead-a.pos[1]
        aim = [math.atan2(ey,ex), math.atan2(me.pos[2]+me.height*.5-a.pos[2]-a.stats["muzzle_height"],max(1.,math.hypot(ex,ey)))]
        sight = self.layout.clear((*a.pos[:2],a.pos[2]+7),(*me.pos[:2],me.pos[2]+me.height*.5))
        fire = active and sight and d<202
        w = a.weapons[1]
        secondary = False
        if fire and w:
            if w["kind"] == "laser":
                secondary = w["charge"] < w["stats"]["charge"]
            elif w["kind"] == "lightning":
                secondary = d < w["stats"]["range"]
            elif 24 < d < 165 and w["cooldown"] < .11:
                aim[1] += .5*math.asin(min(1.,d*w["stats"]["gravity"]/w["stats"]["speed"]**2))
                secondary = True
        return dict(move=[dx*speed,dy*speed], aim=aim, fire=[fire,secondary])

    def move(self, a, action):
        st, dt = a.stats, self.dt
        desired = action.get("aim",a.aim)
        a.aim[0] = wrap(a.aim[0]+clamp(wrap(desired[0]-a.aim[0]),-st["turn_rate"]*dt,st["turn_rate"]*dt))
        pitch = clamp(desired[1],st["min_pitch"],st["max_pitch"])
        a.aim[1] += clamp(pitch-a.aim[1],-st["pitch_rate"]*dt,st["pitch_rate"]*dt)
        if action.get("jump") and a.grounded:
            a.vel[2],a.grounded=st["jump_speed"],False
        x,y = action.get("move",(0.,0.))
        norm = math.hypot(x,y)
        boost = action.get("boost") and a.energy > dt*max(st["jet_drain"],st["boost_drain"]) and (norm>.01 or not a.grounded)
        speed = st["boost_speed"] if boost and a.grounded else st["walk_speed"]
        if any(w and w.get("charge",0)>0 for w in a.weapons):
            speed *= st["charge_move_mult"]
        dx,dy=x*speed/max(norm,1.)-a.vel[0], y*speed/max(norm,1.)-a.vel[1]
        k=min(1.,dt*(st["ground_accel"] if a.grounded else st["air_accel"])/max(.001,math.hypot(dx,dy)))
        a.vel[0]+=k*dx
        a.vel[1]+=k*dy
        for i in (0,1):
            p=a.pos.copy()
            p[i]+=dt*a.vel[i]
            if self.layout.walk(*p,a.radius):
                a.pos[i]=p[i]
            else:
                a.vel[i]=0.
        floor=self.layout.surface(*a.pos[:2])
        if floor>a.pos[2]+st["step_up"]:
            floor=self.layout.ground(*a.pos[:2])
        a.grounded=a.pos[2]<=floor+.03 and a.vel[2]<=0
        if not a.grounded:
            a.vel[2]=min(st["max_rise_speed"],a.vel[2]+dt*((st["jet_accel"] if boost else 0)-st["gravity"]))
        a.pos[2]=max(floor,a.pos[2]+dt*a.vel[2])
        if a.pos[2]<=floor+.001 and a.vel[2]<=0:
            a.vel[2],a.grounded=0.,True
        if boost:
            a.energy-=dt*(st["boost_drain"] if a.grounded else st["jet_drain"])
            a.last_cost=self.now
        elif self.now-a.last_cost>=st["energy_regen_delay"]:
            a.energy=min(st["energy"],a.energy+st["energy_regen"]*dt)
        a.zone_ok = horizontal(a.pos,self.zone["center"])<=self.zone["radius"]
        if not a.zone_ok:
            self.hit(None,a,"zone",dt*self.zone["dps"])
        elif self.now-a.last_damage>=st["regen_delay"]:
            a.hp=min(a.max_hp,a.hp+st["regen_per_s"]*dt)

    def hit(self, src, dst, kind, damage):
        if dst.hp<=0:
            return
        bearing=None if src is None else self.bearing(dst,src)
        rear=False
        if src:
            damage*=1+min(src.cubes,self.cfg["cubes"]["stat_cap"])*self.cfg["cubes"]["damage_per_cube"]
            if dst.kind=="mech":
                rear=abs(wrap(bearing-dst.aim[0]))>math.radians(dst.stats["front_arc_deg"]*.5)
                damage*= (dst.stats["rear_mult"] if rear else 1)*(1-dst.stats["armor"])
            src.events.append(dict(type="hit",target=dst.id,amount=damage,weapon=kind,rear=rear))
            src.last_damage=self.now
            dst.hunting=True
            if src is self.player and dst is not src and dst.kind=="mech":
                self.dealt+=min(dst.hp,damage)
        if dst is self.player:
            self.taken+=min(dst.hp,damage)
            if kind=="zone":
                self.zone_damage+=min(dst.hp,damage)
        dst.hp-=damage
        dst.last_damage=self.now
        dst.events.append(dict(type="damaged",amount=damage,weapon=kind,bearing=bearing,
                               by=src.id if src else None,rear=rear))
        if dst.hp>0:
            return
        if dst.kind=="mech":
            self.dead[dst.id]=self.now
            if src is self.player and dst is not src:
                self.kills+=1
                src.events.append(dict(type="kill",target=dst.id))
        n = dst.cubes+self.cfg["cubes"]["death_drop_extra"] if dst.kind=="mech" else self.cfg["npc" if dst.kind=="npc" else "crates"]["cubes"]
        for j in range(n):
            self.next_id+=1
            self.cubes.append(dict(id=self.next_id,pos=[dst.pos[0]+j*.4,dst.pos[1],dst.pos[2]]))
        if dst.kind=="crate" and dst.rng.random()<self.cfg["loot"]["crate_weapon_chance"]:
            self.next_id+=1
            self.pickups.append(dict(id=self.next_id,kind=dst.rng.choice(("laser","lightning","mortar")),pos=dst.pos.copy()))

    @staticmethod
    def contact(a,b,target,radius):
        dx,dy=b[0]-a[0],b[1]-a[1]
        p=target.pos
        f=clamp(((p[0]-a[0])*dx+(p[1]-a[1])*dy)/max(.00001,dx*dx+dy*dy),0.,1.)
        z=a[2]+(b[2]-a[2])*f
        if abs(p[2]+target.height*.5-z)>target.height*.5+radius:
            return None
        return f if math.hypot(a[0]+f*dx-p[0],a[1]+f*dy-p[1])<=target.radius+radius else None

    def targets(self, owner):
        # Rivals cooperate. Drones defend themselves against the player alone.
        if owner is self.player:
            return [a for a in self.actors.values() if a is not owner and a.hp>0]
        return [self.player] if self.player.hp>0 else []

    def fire(self,a,action):
        dt=self.dt
        for i,w in enumerate(a.weapons):
            if not w:
                continue
            k,st=w["kind"],w["stats"]
            w["cooldown"]=max(0.,w["cooldown"]-dt)
            held=action.get("fire",(False,False))[i]
            if k=="gun":
                if w["reload"]>0:
                    w["reload"]=max(0.,w["reload"]-dt)
                    if w["reload"]<1e-8:
                        w["ammo"]=st["mag"]
                        w["reload"]=0.
                    continue
                if w["ammo"]<=0 or (action.get("reload") and w["ammo"]<st["mag"]):
                    w["reload"]=st["reload"]
                    continue
            if w["cooldown"]>1e-8:
                continue
            power=1.
            if k=="laser":
                if held and w["charge"]<st["charge"]+st["hold_s"]:
                    w["charge"]+=dt
                    continue
                if w["charge"]<=0:
                    continue
                power=st["min_frac"]+(1-st["min_frac"])*clamp(w["charge"]/st["charge"],st["min_charge"]/st["charge"],1.)
                w["charge"]=0.
            elif not held:
                continue
            yaw,pitch=a.aim
            if k=="gun":
                spread=math.radians(st["spread_deg"])
                yaw+=a.rng.gauss(0,spread)
                pitch+=a.rng.gauss(0,spread)
                w["ammo"]-=1
            if k=="lightning":
                if a.energy<st["energy"]:
                    continue
                a.energy-=st["energy"]
                a.last_cost=self.now
            w["cooldown"]=st["cooldown"]
            ray=(math.cos(yaw)*math.cos(pitch),math.sin(yaw)*math.cos(pitch),math.sin(pitch))
            z=a.height+.5 if k=="mortar" else a.stats["muzzle_height"]
            origin=[a.pos[j]+(a.radius+.5)*ray[j]+(z if j==2 else 0) for j in range(3)]
            if a is not self.player and self.player.hp>0:
                d=horizontal(a.pos,self.player.pos)
                if d<self.cfg["sound"]["range"][k]:
                    self.player.sounds.append(dict(kind=k,age=0.,dist="near" if d<60 else "mid" if d<160 else "far",
                                                   bearing=self.bearing(self.player,a)+a.rng.gauss(0,.12)))
            if k in ("gun","mortar"):
                self.launch(a,k,origin,[v*st["speed"] for v in ray],st)
                continue
            hits=[]
            end=[origin[j]+ray[j]*st["range"] for j in range(3)]
            for target in self.targets(a):
                body=(*target.pos[:2],target.pos[2]+target.height*.5)
                if not self.layout.clear(origin,body):
                    continue
                d=math.dist(origin,body)
                if k=="lightning":
                    accepted = d<=st["range"] and abs(wrap(self.bearing(a,target)-yaw))<=math.radians(st["cone_deg"])
                else:
                    accepted = self.contact(origin,end,target,0.) is not None
                if accepted:
                    hits.append((d,target.id,target))
            if hits:
                target=min(hits)[2]
                self.hit(a,target,k,power*st["damage"])

    def launch(self,owner,kind,pos,vel,stats):
        self.next_id+=1
        ttl=stats["ttl"] if "ttl" in stats else stats["range"]/max(1.,math.hypot(*vel))
        self.shots.append(dict(id=self.next_id,owner=owner.id,kind=kind,pos=pos,vel=vel,ttl=ttl,stats=stats))

    def step_shots(self):
        remain=[]
        for shot in self.shots:
            a=shot["pos"]
            b=[a[j]+self.dt*shot["vel"][j] for j in range(3)]
            owner,st,k=self.actors[shot["owner"]],shot["stats"],shot["kind"]
            if k=="mortar":
                shot["vel"][2]-=st["gravity"]*self.dt
            blocked=b[2]<=self.layout.ground(*b[:2]) or not self.layout.clear(a,b)
            hits=[]
            for target in self.targets(owner):
                f=self.contact(a,b,target,self.cfg["projectile"].get(k+"_radius",0))
                if f is not None:
                    hits.append((f,target.id,target))
            if hits:
                f,_,target=min(hits)
                impact=[a[j]+(b[j]-a[j])*f for j in range(3)]
                if self.layout.clear(a,impact):
                    self.hit(owner,target,k,st["damage"])
                    b=impact
            shot["ttl"]-=self.dt
            if not hits and not blocked and shot["ttl"]>0:
                shot["pos"]=b
                remain.append(shot)
            elif k=="mortar":
                for target in self.targets(owner)+[owner]:
                    dist=horizontal(b,target.pos)
                    if dist<st["splash_radius"] and abs(b[2]-target.pos[2]-target.height*.5)<st["splash_radius"]+target.height*.5:
                        factor=1-(1-st["splash_edge"])*dist/st["splash_radius"]
                        self.hit(owner,target,k,st["splash"]*factor*(.5 if target is owner else 1))
        self.shots=remain

    def collect(self,a,action):
        for item in self.pickups[:]:
            if item["id"]!=action.get("take") or horizontal(a.pos,item["pos"])>self.cfg["loot"]["pickup_radius"] or abs(a.pos[2]-item["pos"][2])>4:
                continue
            if any(w and w["kind"]==item["kind"] for w in a.weapons):
                continue
            slot=action.get("drop")
            if slot is None:
                slot=next((i for i,w in enumerate(a.weapons) if not w),None)
            if slot not in (0,1) or (a.weapons[slot] or {}).get("charge",0)>0:
                continue
            a.equip(slot,item["kind"],self.cfg,self.cfg["loot"]["equip_s"])
            self.pickups.remove(item)
            a.events.append(dict(type="took",id=item["id"],kind=item["kind"],slot=slot))
        for cube in self.cubes[:]:
            if horizontal(a.pos,cube["pos"])>self.cfg["cubes"]["pickup_radius"] or abs(a.pos[2]-cube["pos"][2])>4:
                continue
            self.cubes.remove(cube)
            a.cubes+=1
            rules=self.cfg["cubes"]
            if a.cubes<=rules["stat_cap"]:
                dh=self.cfg["mech"]["hp"]*rules["hp_per_cube"]
                a.hp+=dh
                a.max_hp+=dh
            a.events.append(dict(type="pickup",cubes=a.cubes))
            if a.cubes in rules["upgrade_thresholds"] and a.offer is None:
                ids=("armor","plating","gun_damage")
                a.offer=dict(id=a.cubes,expires=self.now+5,choices=[dict(id=v,name=v,desc="") for v in ids])
        if a.offer and ("pick" in action or self.now>=a.offer["expires"]):
            choices=a.offer["choices"]
            index=action.get("pick",0)
            if type(index) is int and 0<=index<len(choices):
                ident=choices[index]["id"]
                a.upgrades.append(ident)
                if ident=="plating":
                    a.hp+=a.max_hp*.15
                    a.max_hp*=1.15
                elif ident=="armor":
                    a.stats["armor"]+=.08
                else:
                    for w in a.weapons:
                        if w and w["kind"]=="gun":
                            w["stats"]["damage"]*=1.15
                a.offer=None

    def drone(self):
        self.drone_actor(self.actors[100])

    def drone_actor(self,a):
        if a.hp<=0 or self.player.hp<=0:
            return
        cfg=self.cfg["npc"]
        d=horizontal(a.pos,self.player.pos)
        if not (d<cfg["aggro_range"] or (a.hunting and d<cfg["deaggro_range"])):
            return
        yaw=self.bearing(a,self.player)
        if d>25 and horizontal(a.pos,a.home)<cfg["chase_leash"]:
            x,y=a.pos[0]+self.dt*cfg["speed"]*math.cos(yaw),a.pos[1]+self.dt*cfg["speed"]*math.sin(yaw)
            if self.layout.walk(x,y,a.pos[2],a.radius):
                a.vel=[(x-a.pos[0])/self.dt,(y-a.pos[1])/self.dt,0]
                a.pos=[x,y,self.layout.ground(x,y)]
        if self.now<a.npc_ready:
            return
        origin=(*a.pos[:2],a.pos[2]+2.5)
        body=(*self.player.pos[:2],self.player.pos[2]+self.player.height*.5)
        if not self.layout.clear(origin,body):
            return
        yaw+=a.rng.gauss(0.,math.radians(cfg["spread_deg"]))
        pitch=math.atan2(body[2]-origin[2],d)
        speed=cfg["projectile_speed"]
        self.launch(a,"npc",list(origin),[speed*math.cos(yaw)*math.cos(pitch),speed*math.sin(yaw)*math.cos(pitch),speed*math.sin(pitch)],dict(damage=cfg["damage"],range=140))
        a.npc_ready=self.now+cfg["cooldown"]

    def run(self, bot, trace):
        me=self.player
        tick=0
        while self.now<self.duration and me.hp>0 and len(self.dead)<len(self.opponents):
            self.update_zone()
            obs=self.obs(tick)
            start=time.perf_counter()
            action=dict(bot.act(obs) or {})
            latency=(time.perf_counter()-start)*1000
            action["tick"]=tick
            decision=copy.deepcopy(getattr(bot,"last_decision",None)) if trace else None
            before=(self.dealt,self.taken,self.zone_damage,self.kills,me.cubes)
            house={i:self.house(self.actors[i]) for i in self.opponents if self.actors[i].hp>0}
            for _ in range(self.stride):
                alive=[a for a in self.actors.values() if a.kind=="mech" and a.hp>0]
                for a in alive:
                    act=action if a is me else house[a.id]
                    self.move(a,act)
                    if a.hp > 0:
                        self.collect(a,act)
                        self.fire(a,act)
                self.drone()
                self.step_shots()
                tick+=1
                self.now=tick*self.dt
                if me.hp<=0 or len(self.dead)>=len(self.opponents):
                    break
            if hasattr(bot,"sent"):
                bot.sent(obs["tick"],action,on_time=True,applied=True)
            if trace:
                trace(obs,copy.deepcopy(action),dict(decision=decision,decision_ms=latency,
                      hp_after=max(0.,me.hp),damage_dealt=self.dealt-before[0],
                      damage_taken=self.taken-before[1],zone_damage=self.zone_damage-before[2],
                      kills=self.kills-before[3],cubes=me.cubes-before[4],events=copy.deepcopy(me.events)))
        if me.id in self.dead:
            place=1+sum(i not in self.dead or self.dead[i]>self.dead[me.id] for i in self.opponents)
        else:
            place=1+sum(self.actors[i].hp>me.hp and i not in self.dead for i in self.opponents)
        end=dict(type="end",place=place,kills=self.kills)
        if hasattr(bot,"end"):
            bot.end(end)
        return dict(score=1+len(self.opponents)-place,place_proxy=place,kills=self.kills,survival_s=self.now,
                    cubes=me.cubes,damage_dealt=self.dealt,damage_taken=self.taken,
                    zone_damage=self.zone_damage,armed=sum(w is not None for w in me.weapons)>1,
                    won=place==1,seed=self.seed,scenario=self.scenario,final_hp=max(0.,me.hp))
