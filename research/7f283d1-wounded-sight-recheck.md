# Recheck cached obstruction for a wounded top target

Tested `7f283d18f0486b91d8776cb59aa4b969355ec007` against `489c7211da0f707e27bba0741abf487fe084871e`. It adds one current-geometry check per observation for a wounded top candidate the bot would engage. A failed recheck retains the prior cache expiration.

| Simulated sample | Pairs | Placement points per game | Improved / tied / worse |
| --- | ---: | ---: | ---: |
| Campus squad, 964001–964024 | 24 | −0.417 | 2 / 19 / 3 |
| Independent campus squad, 964601–964616 | 16 | +0.125 | 1 / 15 / 0 |
| Independent public-upgrade campus, 964701–964716 | 16 | +0.563 | 2 / 14 / 0 |
| Four-mech, 964101–964106 over four scenarios on two maps | 48 | 0.000 | 0 / 48 / 0 |

In owner seed 964006, the recheck switched from mech 2 to mech 15 at 99.9 seconds. Damage dealt fell 93.6 in the next second with no change in damage taken, and placement fell seven places. In independent seed 964609, it acquired a target while the incumbent scanned and later placed two higher. The first-second damage was the same. Across the three campus panels, placements gained a total of one point in 56 games.

A fixed-input archive recorded 812 extra probes and 31 successful rechecks across 10 of 32 games. At most two extra tests occurred while one negative cache entry stayed active. All 24 unit tests and 300 starter-check observations passed, with a 3.2 ms p99.

| Sol reviewer | Practice vote | Reason |
| --- | --- | --- |
| Survival | Revise | Earlier visibility was reproducible, but the original variant interrupted useful contact and the pooled gain was negligible. |
| Combat | Revise | The owner's ten-point total loss and one observed diversion from open fire warrant keeping the incumbent target when available. |
| Validation | Revise | Independent gains were offset by the owner panel, with a specific first-second damage loss when replacing an existing target. |

Test a recheck only when the incumbent search would otherwise scan. This keeps the 964609 trigger and removes the 964006 diversion.
