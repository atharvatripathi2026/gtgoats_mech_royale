# Keep enough ammunition after a pressure return shot

`2015a12cbf9b55b1a590dc80aec427095251e2ba` revises `e3184ebc9732c1f3492c9dfeee231a0c398618f7`. The return-fire rule requires enough ammunition after the possible held trigger to remain at or above the native 80% quiet-reload threshold. The shot count accounts for the current cooldown, the physics cadence and the observed weapon. The effective gameplay comparison is verified `03a8f93fb36afa5db4a08f211d1d1aa6dcbcae8e`. [Earlier return-shot experiment](e3184eb-return-fire-at-live-pressure.md)

| Fresh simulated panel | Seed start | Pairs | Placement change | Improved / tied / regressed |
|---|---:|---:|---:|---|
| Standard campus | 1021101 | 16 | −2 | 0 / 15 / 1 |
| Independent standard campus | 1021301 | 16 | −6 | 0 / 15 / 1 |
| Joint hull and impact | 1021401 | 16 | +10 | 1 / 15 / 0 |
| Four-mech | 1021201 | 48 | 0 | 0 / 48 / 0 |

All 23 unit tests and 300 starter observations passed, with sandbox p99 of 34.5 ms. In the earlier joint 1017703 failure, the reserve guard restores every incumbent action and the original survival outcome. In joint 1017710 it retains 50.4 extra outgoing damage across three seconds with incoming held at 45. The fresh +10 joint game 1021407 added 45 damage at equal 45 incoming during the first three seconds. The two standard placement losses had identical damage over their first three seconds and lost survival later.

All three reviewers voted **revise**. Survival cited the effective readiness repair and the continued split between standard and joint models. Combat cited the direct gun damage benefit alongside the stark later placement spread. Validation cited the three isolated score changes and the need to test the surviving shot rule under stronger opponent-cadence variation. The queue received no candidate.
