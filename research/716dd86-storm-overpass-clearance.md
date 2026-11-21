# Preserve a passable underpass during storm entry

Candidate `716dd861e304da9f74e53cfbac1484391e944ba5` descends from `41425de21c0e2e7bf0c48e0881cd1b0bc5926189`. The old guard used the top of a solid to identify a tall wall. The proposed guard checks the solid interval against head height above the sampled terrain, which distinguishes a wall from a bridge with clearance underneath.

In a directed check with the official campus map and its movement integration, the constructed zone put the bot two metres outside near (−114.88, −61.59). The parent vetoed the north approach and the south heading missed the circle for four seconds. The candidate entered after 0.25 seconds and remained grounded through ten integration steps under 11.35 to 11.40 metres of headroom. Both builds took every one of the same 4,156 actions in the original solid-wall replay 1037615.

All 88 fresh simulated placements and measured endpoints tied against the exact parent across 40 campus and 48 four-mech pairs. The owner's 64 match tapes had identical applied actions. An offline scan of 144 archived campus games found 17 opportunities under fixed recorded actions with no divergence. A second prefilter found no veto in 96 parent tapes and reproduced the true veto at the known checkpoint. All 24 unit tests and 300 timed Docker observations passed.

Survival and combat voted approve because the exact physics check corrects a feasible route while preserving the true wall. Validation voted revise because the zone fixture was constructed and the natural runs showed no activation. Withheld. Next, search fresh campus zone centers that put a real underpass on the route, then check a full match where the chosen heading changes.
