# Retarget a repeatedly confirmed frontal shooter

`fd2608aa51a0c9a7154b94744faf83e4b9530def` tests a torso-target override on `cc7628485b7b5ea5b53f51af18baec5e624bd86a`. Two recent frontal gun hits from the same visible opponent can override the current target when the gun is ready, the source is facing the bot, the muzzle has clearance, and the current target is neither close nor close to a finish. It preserves the first move and the ordinary trigger rules. The override expires quickly and does not change native target stickiness.

| Fresh simulated panel | Seed start | Pairs | Placement-point change | Improved / tied / regressed |
|---|---:|---:|---:|---:|
| Standard campus | 1014001 | 24 | 0 | 0 / 24 / 0 |
| Independent standard campus | 1014301 | 16 | −4 | 0 / 15 / 1 |
| Joint hull and impact campus | 1014401 | 16 | 0 | 0 / 16 / 0 |
| Four-mech | 1014101 | 48 | 0 | 0 / 48 / 0 |

All 25 tests and 300 starter observations passed. Sandbox p99 was 1.5 ms. In 72 archived games the fixed-input replay changed five target frames across four matches and withheld one already-ready gun trigger. Three closed-loop archived probes tied on survival and placement despite modest differences in which opponent was hit.

In fresh seed 1014303, the variant targeted #2 for 0.2 s after #2 dealt two frontal 45 HP hits. The displaced target #6 had also just dealt two 67.5 HP rear hits. The new yaw never acquired #2 before switching back. Incoming damage through three seconds stayed 225 in both. Outgoing dropped from 162 to 113.4 over one second and from 664.2 to 567 over three. The variant lost four placement points.

- Survival voted **reject for practice** because the update favored one source and ignored the competing threat. The only fresh placement change lost four.
- Combat voted **reject for practice** because the gun was ready but the new aim could be outside the first two physics turns. The policy gave up an aligned incumbent without a timely shot.
- Validation voted **reject for practice** because the changed head turn delayed return fire and the archived switching tests produced no placement gain.

Any revisit should require the new shot to align under the actual held trigger window and compare the current target's recent damage before changing aim. The queue received no candidate for this behavior.
