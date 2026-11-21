# Preserve mortar against clusters during a gun finish

`a023b8283786ed2d2b2196dc85150089aa23b72e` revises `e06fdd1f417b8bba0a17df00ac16798af0990869`. The tested baseline is `cc7628485b7b5ea5b53f51af18baec5e624bd86a`. It retains mortar priority when another visible mech approaches the target within splash plus both hull radii before the approximate shell arrival. It conservatively uses lateral separation, including cases with vertical separation or walls. Two-hit and armor estimates from the original policy remain. [Original policy and cluster counterexample](e06fdd1-quicker-gun-finish.md)

| Fresh simulated panel | Seed start | Pairs | Improved / tied / regressed |
|---|---:|---:|---:|
| Standard campus | 1013201 | 16 | 0 / 16 / 0 |
| Independent standard campus | 1013501 | 16 | 0 / 16 / 0 |
| Joint hull and impact campus | 1013401 | 16 | 0 / 16 / 0 |
| Four-mech | 1013301 | 48 | 0 / 48 / 0 |

All 48 campus pairs were identical on measured outcome fields. In one generated crossfire game (1013305) the candidate swung from mortar aim to gun against the same opponent at 49.1 m. The gun killed at 13.6 s instead of 13.7 s, with equal first-second damage in both directions. The variant finished with 76.5 more HP and tied placement. The other 47 four-mech outcomes matched.

Fixed replay of all 3,842 decisions in 990611 kept the original switch at 130.6 s and restored the clustered mortar shot at 289.6 s. The standard closed-loop replay again killed 0.1 s earlier and gained one eventual placement point. With combined hull, impact and wall-splash sensitivity, the fixture reached none of the eligible opportunities and all 1,434 emitted actions matched. [Wall-splash check](2026-11-21T040800Z-mortar-cover-sensitivity.md)

All 25 units and 300 starter observations passed, with sandbox p99 of 1.6 ms.

- Survival voted **reject for practice** because all campus endpoints matched and the known gain was sensitive to arena rules.
- Combat voted **reject for practice** because the 0.1 s faster kills were real but too sparse to show a fresh placement result.
- Validation voted **reject for practice** because the cluster protection passed and all fresh placements tied, while the lethality estimate still assumes armor and turnaround.

The queue received no candidate for this behavior. Keep both the isolated and clustered replays as fixtures for a future weapon policy.
