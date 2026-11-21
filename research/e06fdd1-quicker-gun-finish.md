# Give the ready gun a faster finishing shot

`e06fdd1f417b8bba0a17df00ac16798af0990869` changes aim priority on gameplay parent `cc7628485b7b5ea5b53f51af18baec5e624bd86a`. It can choose an aligned loaded gun over a mortar if one or two estimated hits can finish the target at least 0.15 s before shell arrival. It uses the existing trigger rules with the newly chosen aim, which can withhold the mortar trigger. A fixed 20% armor discount, clean center ray and approximate flight times are proxies for a lethal intercept.

| Fresh simulated panel | Seed start | Pairs | Placement-point change |
|---|---:|---:|---:|
| Standard campus | 1012001 | 24 | 0, all tied |
| Independent standard campus | 1012801 | 16 | 0, all tied |
| Joint hull and impact campus | 1012901 | 16 | 0, all tied |
| Four-mech | 1012101 | 48 | 0, all tied |

The patch passed all 25 units and 300 starter observations at p99 23.9 ms. Five switches occurred in 167,036 archived observations. In controlled seed 990611 at 130.6 s the first changed shot finished the same opponent at 130.8 s rather than 130.9 s. No incoming damage changed during that exchange and the candidate gained one eventual placement point.

At 289.6 s in the original replay, the fixed-input change suppresses the mortar against the 2.1 HP target with three opponents nearby. The original mortar produced 1093.2 combined simulated direct and splash damage to four opponents. That counterexample prompted the [cluster-aware revision](a023b82-isolated-gun-finish.md). Local wall coverage affects estimates of collateral damage. [Mortar cover sensitivity](2026-11-21T040800Z-mortar-cover-sensitivity.md)

- Survival voted **reject for practice** because all fresh placements tied and the faster kill appeared in a single known diagnostic.
- Combat voted **revise** because the intended short-window benefit is real but the exact gate sacrifices the multi-target mortar shot.
- Validation voted **revise** because the estimated one- or two-round finish overlooks the collateral value and does not prove actual lethality.

The queue received no candidate for this behavior.
