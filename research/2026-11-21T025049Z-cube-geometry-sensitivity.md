# Local sensitivity to cube-driven hull growth

The public rules give hull radius, height, eye height and muzzle height uncapped growth of 5% per cube, even after the health and damage cap of ten. The public-upgrade simulator previously held those dimensions constant. An isolated diagnostic commit `e7690a84148204fcf96efc183819b13408585ffe` under `/tmp/gtg-cube-size-aX2bax` implements that growth for the player and house mechs, including the changed heights in house sight and aim. The code is preserved locally on `research/public-cube-geometry`. All 38 tests passed. [Public rules](https://www.joinbuilders.org/buildathon/tracks/builders/files/protocol.md)

| Public-upgrade campus model, matched seeds 971801–971816 | Exact 3.71 official reference `03a8f93` | Queued gun-throughput `367287e` | Relative placement difference |
| --- | ---: | ---: | ---: |
| Fixed hull | 9.375 | 10.438 | +1.063 |
| Scaled hull | 7.875 | 8.938 | +1.063 |

Both simulated scores fell by 1.5. The same mean difference hides changes in individual outcomes. The baseline held 9.12 cubes on average under fixed geometry and 6.31 with scaling; throughput went from 11.75 to 9.56. The geometry remains rasterized, house lead still uses the base gun speed, and the engine omits mech-to-mech pushing. Use the scaled panel as an independent stress test, with separate results from the existing evaluator.
