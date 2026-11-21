# Prefer shorter torso turns when targeting a squad

All three Sol reviewers voted **reject** on `f87c5a41f2d68ee221e9dc9f0a8da7f3e8beb75c` against squad focus. The candidate penalizes the estimated time spent rotating to engage a squad target. It keeps the existing alignment weight outside squad engagements.

| Fresh local panel | Mean placement change | Improved / tied / regressed |
| --- | ---: | ---: |
| Campus squad, 24 | −0.083 | 1 / 20 / 3 |
| Independent campus squad, 16 | +0.125 | 1 / 15 / 0 |
| Four-mech, 48 | −0.021 | 0 / 47 / 1 |

On independent seed 933808 the candidate fired 0.3 seconds sooner by staying aligned with a farther opponent. It later changed paths, picked up a laser and gained two placement points even though it died sooner. The earlier 913305 replay had already aligned the torso with the selected wounded rival, so the new score did not change that case. The owner and independent squad gains and losses netted to zero.

All 23 unit tests and 300 official replay observations passed. Target turn time alone did not improve placement in the fresh samples.
