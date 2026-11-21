# Preferred range in isolated engagements

A local parameter search tested seven changes to squad focus `c1456b52088811a77a41473c50c4c70faa81d2e4` across two discovery panels of 12 simulated squad seeds each. The default beat alternatives changing resource priority, stronger separation, pressure credit, or preferred ranges of 56, 84 and 108 metres. The 72-metre setting gained 0.250 points over the 78-metre default in discovery. A single 12-point improvement drove the gain.

All three Sol reviewers voted **reject** on exact frozen commit `bb40cf4987cabe7b2a78a95de6eaa49cfff534a4`.

| Fresh local panel | Mean placement change | Improved / tied / regressed |
| --- | ---: | ---: |
| Campus squad, 24 | −1.458 | 7 / 7 / 10 |
| Independent campus squad, 12 | −1.750 | 4 / 2 / 6 |
| Four-mech, 48 | +0.125 | 6 / 40 / 2 |

The move is coupled to three effects: the range where adaptation is allowed contracts from 133 to 127 metres, the pressure to press increases between 72 and 78 metres, and distance preference changes when pressing. A fixture at 74 metres with an injured mech switched from spacing to pressing. The result suggests testing those effects separately if this policy is revisited.

All 23 unit tests and 300 official replay observations passed. The replay measured 4.6 ms p99 decision time.
