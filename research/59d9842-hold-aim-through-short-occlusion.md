# Retain aim briefly when the engaged target goes behind cover

`59d98422dc42d65f40636e76957c55928b3b80ab` descends from verified `03a8f93fb36afa5db4a08f211d1d1aa6dcbcae8e`. When no target passes the normal visibility search but the last engaged rival remains tracked, the bot can hold the prior torso aim for up to 0.65 seconds. A loaded gun, no active charge, and no conflicting recent damage or nearby combat sound are required. Native legs, triggers and reload rules stay in place on the changed observation.

| Fresh simulated panel | Seed start | Pairs | Placement change | Improved / tied / regressed |
|---|---:|---:|---:|---:|
| Standard campus | 1019401 | 24 | −28 | 1 / 18 / 5 |
| Independent standard campus | 1020101 | 16 | +6 | 2 / 13 / 1 |
| Joint hull and impact | 1020201 | 16 | +3 | 1 / 14 / 1 |
| Four-mech | 1019501 | 48 | 0 | 0 / 48 / 0 |

All 23 unit tests and 300 starter observations passed, with sandbox p99 of 2.6 ms. Fixed replay of 80 matches found 145 hold episodes, including 28 quick returns to the same target, and no blind-fire change on held frames.

In 1014215 the first gun shot after return advanced from 25.7 to 25.2 s and added 90 same-target damage. The extra shots lowered the magazine to 8/12 and led to a native reload during the next gap, leaving the gun unavailable on the second return. The run lost one placement point. In joint 1014204 an earlier shot added 91.8 outgoing damage over one second and the run also lost a point. A fresh owner loss, 1019401, demonstrates a separate cost. Holding the previous aim let a different opponent stay unobserved 0.2 seconds longer and delayed the next gun trigger by the same interval.

All three reviewers voted **reject for practice**. The directed shots confirm a genuine timing benefit. The hold occurred much more often than the same foe returned, constrained scanning and could advance a later voluntary reload. The queue received no candidate.
