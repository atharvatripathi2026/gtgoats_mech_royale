# Joint sensitivity to hull growth and incoming hit direction

Local tool commit `d41e20c7cb47b06b3980a459e799108396d66550` in `/tmp/gtg-cube-impact-asaJk8` combines the separate hull-growth and impact-direction experiments. It passed 39 tests and is preserved on the local `research/combined-arena` ref. Other rasterized movement and approximate blast assumptions remain. [Hull rules study](2026-11-21T025049Z-cube-geometry-sensitivity.md) · [Impact rules study](2026-11-21T030538Z-impact-bearing-calibration.md)

| Simulated comparison | Pairs | Placement points per game |
| --- | ---: | ---: |
| Second-tick `cc76284` vs gun-upgrade `8b9f76d`, both rules, fresh 1000601–1000624 | 24 | −0.042 |
| `367287e` vs `8b9f76d`, scaled hull alone, 981301–981324 | 24 | −0.250 |
| Same families and seeds, scaled hull plus impact bearing | 24 | +1.333 |

The second-tick trial against its own parent had two gains, 20 ties and two losses. The joint rule changes reversed the mean ordering between the two full gun-upgrade families on the earlier matched seed set. Under both rules, 11 favored `367287e`, nine tied, and four favored `8b9f76d`. This sensitivity warrants keeping both families active and motivates testing the second-tick timing directly on `367287e`, under the usual arena and the joint holdout.
