# Keep the imminent line dodge during a finish

All three reviewers voted revise on `873281e56fffcc991a9ed1288e23627a9f4867e6`. Its gameplay parent is `cc7628485b7b5ea5b53f51af18baec5e624bd86a`. The policy preserves the existing dodge when an alternative finishing flank would reduce projected clearance for a visible imminent direct shot. It leaves weapon selection and timing unchanged.

| Simulated panel | Seed start | Pairs | Placement-point change | Improved / tied / regressed |
|---|---:|---:|---:|---:|
| Standard campus | 1010401 | 24 | 0 | 3 / 20 / 1 |
| Independent standard campus | 1010801 | 16 | +8 | 2 / 14 / 0 |
| Joint hull and impact campus | 1010901 | 16 | −4 | 1 / 14 / 1 |
| Four-mech | 1010501 | 48 | 0 | 0 / 48 / 0 |

All 25 units and 300 starter observations passed. The sandbox p99 was 17.7 ms. Fixed observations in 72 prior simulated matches produced 20 flank suppressions across 12 games. The affected seed 1010404 avoided 45 incoming damage and dealt the same damage over three seconds. At seed 1010402 both versions took the first 45 damage, then the change took 65.9 more incoming and dealt 50.4 less outgoing through three seconds. That match lost eight placement points. The known joint replay 1000609 also took the original 67.5 damage hit before later trade diverged and lost six placement points.

- Survival voted **revise** because point clearance ignores realized steering and charge changes, and the joint model gave back part of the standard benefit.
- Combat voted **revise** because one demonstrated save coexisted with worse retaliation and weaker outgoing damage in the largest loss.
- Validation voted **revise** because the largest loss preserved the original hit, while changing the flank sharply enough to worsen the following exchange.

Next require a tracked incoming player projectile whose collision differs under the realized steering alternatives. Keep seeds 1010404 and 1010402 as positive and negative fixtures before sampling fresh placement. The queue received no candidate for this behavior.
