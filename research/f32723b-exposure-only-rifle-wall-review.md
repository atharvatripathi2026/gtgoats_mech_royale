# Gate rifle wall checks on evade movement · revise

Exact `f32723bb0424d11c7b642d141b24ef21a3631a07` adds a native avoid-exposure check to the [earlier threshold guard](5f13d6d-rifle-reload-threshold-review.md). It admits only the existing evade route without an active dodge or another movement override. The stock comparator was `15aff403bd7773b312fdfd9bc7e3765714acd7bd`.

Directed 1073492 preserves the 100.8 outgoing gain and 1074011 keeps the quiet reload. The previous immediate-reload 1074064 matches stock commands. In the eight fresh campus pairs 1074110–17, seven match every command and placement. In 1074114 at 25.6, the guard holds a rifle at 8/12 rounds. Both bots start the same refill at 25.7 while the evade mode persists. The first six seconds tie at 45 outgoing and zero incoming. Placement falls 7→6 despite two seconds of additional life.

All three Sol reviewers voted **revise**. Native evasion can continue through a quiet reload and cannot identify on its own whether the saved round will help. The ammo-only revision matches every stock command in 1074114. Full traces remain local. [Selected ammo guard](fab4926-rifle-wall-above-topoff.md)
