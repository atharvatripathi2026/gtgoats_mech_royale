# Local upgrade offer calibration

Frozen local tooling `8c44d0daf18c5ed648225963d9f93534ea09b01f` in `/tmp/sol-public-upgrades` adds `--public-upgrades` to the optional sixteen-mech campus comparison. It draws distinct eligible choices with a separate seeded per-mech random stream, queues cube thresholds, applies expiry defaults and enforces weapon eligibility and stack limits. The original evaluator remains the default. All 37 tests passed including five focused rules tests. This trial stays outside the practice queue.

| Simulated matched bots | Seeds | Legacy points per game | Revised points per game |
| --- | --- | --- | --- |
| Magazine/sidestep `489c721` vs squad focus `c1456b5` | 961801–961812 | 10.000 vs 9.250 | 9.417 vs 9.167 |
| Confirmed 3.71 commit `03a8f93` vs magazine/sidestep `489c721` | 962701–962716 | 8.938 vs 8.625 | 8.375 vs 8.313 |

Across the 24 logged games in the first row, the prior evaluator selected plating 74 times, reached six stacks, and exceeded the public cap of three in 12 episodes. The revised evaluator selected it 16 times and never exceeded two. Nanites and armor appeared 22 and 14 times. The two matched rankings stayed in the same order on their own seeds, with narrower gaps under the revised offers. The magazine/sidestep branch's lead over squad focus in one panel does not settle its position against the official 3.71 reference.

Maintain both benchmarks when testing a policy that depends on weapon or repair upgrades. The starter replay contains zero cubes in every observation. Offer sampling and the simulated opponents are approximations. The comparison currently models the published choices and stack limits while holding the rest of the local arena fixed.
