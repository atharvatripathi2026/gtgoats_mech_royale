# Check ground legs before treating a cube detour as inexpensive

Tested `d8b57b589fa8ea298b84ad85521d6e978d0c4917` against gameplay base `367287e` and prior revision `5032b43`. When the native route is directly traversable, both legs through the cube must be traversable before the variant uses the inexpensive-detour rule. If the native line is obstructed, the variant retains its previous estimate. The new check rejects the blocked-cube fixture and retains the known 972112 cheap pickup, eventual upgrade and win with identical actions.

| Simulated comparison | Pairs | Placement points per game | Improved / tied / worse |
| --- | ---: | ---: | ---: |
| Vs 367287e, public fixed hull, 982001–982016 | 16 | +0.313 | 2 / 13 / 1 |
| Vs 367287e, independent fixed hull, 982301–982316 | 16 | +0.063 | 1 / 15 / 0 |
| Vs 367287e, independent scaled hull, 982201–982216 | 16 | 0.000 | 0 / 16 / 0 |
| Vs 367287e, four-mech, 982101–982106 on both maps | 48 | 0.000 | 0 / 48 / 0 |
| Vs 5032b43, replayed 980801–980816 | 16 | 0.000 | 0 / 16 / 0 |

The first three panels gained six total places, but omitting the nine-place owner gain changes the mean to −0.064 across the remaining 47. Each owner placement change began with a large detour skip already present in the prior revision. In independent seed 982312, first-second damage tied after a skipped cube and the candidate eventually gained one place. The wall-specific rule has a verified fixture and no demonstrated incremental placement gain. All 24 unit tests and 300 starter-check observations passed.

Survival and validation voted **approve for practice** based on the repaired geometry and the pooled paired gains against the gameplay base. Combat voted **reject** because all direct placements tied the earlier estimate, leaving no measured incremental gain. Withhold both detour experiments. If revisited, measure actual path costs for both routes around nearby obstacles before extrapolating from the straight line.
