# Test recently seen recovery cubes after an elimination

Exact `bf68ef66da882e350e7f043222b6cb62f372ea0c` against `6a9e8bedb98563aa6b2fbcf1bb136a053c355777` brings a compact cube pair back into native loot ranking when the mech is injured, a player kill is recent, and the cubes were visible within .35 seconds. It waits for the normal calm loot branch, no tracked player foes, and a clear same-level path.

Directed pursuit1065691 preserved the earlier rifle carry and collected both cubes after the native controller pursued a weapon. Placement went from 1 to 2 and life from 31.55 to 45 seconds. Independent actor ordering reproduced both pickups. The route choice changed offense and exposure over the next six seconds. All 96 fresh placements tied, and 23 units passed. The loaded networkless checker passed with one late reply.

Survival and combat voted revise because eligible packs entered ordinary loot memory even if the route chose a different item. Validation approved the known pickup benefit and documented the longer native cache. A transient-only control lost both pickups because the pack was hidden from t19.3 through t19.9. The narrower variant ranks transient options and adds only the chosen target to ordinary memory, which bridges the sight gap until the pack returns at t20.0.
