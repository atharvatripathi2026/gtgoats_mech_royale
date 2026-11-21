# Cap predicted gun lead near a ground obstruction

Tested `283b1aa92034b0a4e9269b1781d4ca19f8c1608c` against `cc762848`. When a near-ground opponent's predicted path enters solid geometry, the trial uses the open portion of the horizontal segment. A fixed archive proxy reported 102.88 m total lateral error falling to 81.10 m over 43 such observations. The proxy excludes a target changing direction or sliding along a wall.

| Simulated sample | Pairs | Placement points per game | Improved / tied / worse |
| --- | ---: | ---: | ---: |
| Public upgrades, 1000401–1000424 | 24 | −0.042 | 2 / 21 / 1 |
| Independent public upgrades, 1000901–1000916 | 16 | +0.125 | 1 / 15 / 0 |
| Independent hull growth and impact direction, 1001001–1001016 | 16 | 0.000 | 0 / 16 / 0 |
| Legacy four-mech, 1000501–1000506 on both maps | 48 | 0.000 | 0 / 48 / 0 |

In 1000422 a changed aim yielded 46.8 more outgoing damage over three seconds and later gained four places. In 1000401 the first shot change had equal immediate damage. By three seconds the candidate had dealt 59.4 less after switching targets and eventually lost nine places. The earlier strong archived lead correction on 990615 produced equal hits and placement in closed loop. All 25 tests and 300 starter-check observations passed.

Combat and validation voted **revise** because the center ray can mistake tangential travel for a stop and the fresh effects were mixed. Survival voted **reject** because one large regression offset the favorable placements across models. Preserve full lead for trajectories that may follow an obstacle. Use observed same-target misses and physical clearance to identify better evidence before another variant.
