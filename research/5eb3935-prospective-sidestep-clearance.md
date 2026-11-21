# Require predicted body clearance before a sidestep

All three GPT-6.2 Sol reviewers voted **reject** for practice on `5eb3935a548be9beab1c1b97dee599754eb12a22` against the standalone sidestep parent `e0e641aeea2223f7a8dc6760188d4e2a939cd8eb`. The candidate skips a predictive sidestep when every improved alternative still crosses the estimated body radius. The ordinary projectile response remains available.

Fresh tracing found that emitted headings matched the planner on all 47 observed activations. Archived traces also showed exact heading agreement on 38 activations. A few 100ms displacements continued in the opposite direction while the mech decelerated. That finding alone does not identify a navigation error. Two archived commands were rejected by the new rule because their estimated clearances were only 1.70 and 2.03 metres for a 2.50 metre body radius.

| Paired local panel | Mean placement change | Improved / tied / regressed |
| --- | ---: | ---: |
| Campus squad, 24 | +0.125 | 5 / 14 / 5 |
| Independent campus squad, 20 | −0.500 | 0 / 17 / 3 |
| Four-mech, 48 | +0.021 | 5 / 39 / 4 |

On independent seed 921806 the filter changed the route at 238.8 seconds. Both bots had equal HP 1.3 seconds later, after which their positions and targets diverged. The new candidate finished ninth and the parent first. The replay confirms route sensitivity without establishing which immediate move would have dodged the shot.

The candidate passed 23 unit tests and all 300 official replay observations. A later prediction experiment can account for the opponent projectile's radius and a charged laser's movement penalty, one factor at a time.
