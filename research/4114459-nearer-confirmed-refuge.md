# Reach nearby verified cover after confirmed gun hits

`411445939bcb21911f7aef19b94ed1261452dfa7` builds on verified `03a8f93fb36afa5db4a08f211d1d1aa6dcbcae8e`. A wounded evader under recent confirmed gun fire can choose a nearer waypoint that blocks two hull-height rays from each known recent attacker. It searches clear ground routes inside the current and forecast circle, and can retain the waypoint for up to 1.5 seconds. Emergency projectile dodges take precedence. Cached cover does not re-evaluate the moving shooter every observation.

| Fresh simulated panel | Seed start | Pairs | Placement-point change | Improved / tied / regressed |
|---|---:|---:|---:|---:|
| Standard campus | 1015601 | 24 | +9 | 1 / 23 / 0 |
| Independent standard campus | 1016501 | 16 | −4 | 1 / 13 / 2 |
| Joint hull and impact | 1016601 | 16 | +1 | 1 / 14 / 1 |
| Four-mech | 1015701 | 48 | 0 | 0 / 48 / 0 |

All 22 units and 300 starter observations passed, with sandbox p99 of 43.7 ms under concurrent load. In archived joint 1014215, the refuge saved 225 incoming damage over three seconds but gave up 270 outgoing and lost eight placement points. The sole owner gain, 1015607, added nine points with identical first-six-second damage. In the fresh +1 replay 1016505 the variant sheltered from identified #15 but an unobserved #8 fired from another angle. Over three seconds damage taken rose from 295 to 362.5 and outgoing fell from 108 to 54. A different fresh loss, 1016515, saved 41.4 incoming at equal outgoing and still lost two placement points.

- Survival voted **revise** because the cover endpoint does not preserve firing lanes or account for newly observed rivals.
- Combat voted **revise** because the cached choice can outlast useful occlusion and boost is computed from the original goal.
- Validation voted **revise** because the benefit was concentrated in one placement gain without a better initial exchange. Measure route arrival and return-fire visibility together.

The queue received no candidate for this behavior.
