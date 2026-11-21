# Keep inexpensive post-cap cube detours

Tested `5032b43e56b777a7468c212ff412b0fd457cdecd` against `367287e08745649c728a9cbee2ad2311ac781156`. The trial keeps cheap partial pickups once the HP and damage cap is reached. Detours adding over 19 m to the straight-line route toward the native zone goal require a nearby group rich enough for another upgrade.

| Simulated sample | Pairs | Placement points per game | Improved / tied / worse |
| --- | ---: | ---: | ---: |
| Public upgrades fixed hull, 980001–980024 | 24 | −0.208 | 1 / 21 / 2 |
| Independent fixed hull, 980801–980816 | 16 | +0.625 | 5 / 9 / 2 |
| Independent scaled hull, 980601–980616 | 16 | +0.125 | 1 / 15 / 0 |
| Legacy four-mech, 980101–980106 on both maps | 48 | 0.000 | 0 / 48 / 0 |

The candidate repaired [the earlier 972112 regression](ae029c5-post-cap-cube-detours.md). Both sides kept the same first cube at 77.6 seconds, reached the next upgrade at 138.6 and won. The new route later skipped another cube and took 120 HP more in the full replay. In owner seed 980006, the first skip showed equal outgoing and incoming damage over three seconds and eventually lost five places. The independent fixed-hull panel included five gains with equal immediate damage and two one-place losses. A fixed observation established that a cube can look inexpensive on straight-line geometry even though the direct ground segment is blocked. All 24 tests and 300 starter-check observations passed.

| Sol reviewer | Practice vote | Reason |
| --- | --- | --- |
| Survival | Approve for practice | The earlier low-cost route was restored and both independent cohorts improved. The small pooled gain and owner regression limit confidence. |
| Combat | Approve for practice | The exact patch repaired the earlier scaled-hull failure and both independent means were positive. |
| Validation | Revise | The aggregate +0.125 across 56 is uncertain, and a blocked segment defeats the cost estimate in a concrete fixture. |

Withhold this exact version. Check the cheap route against the actual ground segment before another comparison.
