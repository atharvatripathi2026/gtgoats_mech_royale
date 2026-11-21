# Local house decision cadence sensitivity

The default campus surrogate updates its house commands every 0.5 seconds. An isolated one-line tooling commit `c832f16ee9fe92787190ef72f53706028d5cc075` under `/tmp/gtg-house-cadence-JqrXSq` shortened it to 0.2 seconds. All controller bytes, arena setup and seeds are paired within each model. The faster cadence also changes when the house observes the player and draws aiming variation.

| Simulated house cadence, seeds 965801–965816 | Confirmed 3.71 commit `03a8f93` | Magazine/sidestep `489c721` | Relative difference |
| --- | ---: | ---: | ---: |
| Default 0.5s | 10.125 | 10.750 | +0.625 |
| Faster 0.2s | 9.063 | 9.563 | +0.500 |

Both scores fell, and the mean ordering held on this 16-seed panel. Another [16-seed panel](2026-11-21T022130Z-upgrade-model-calibration.md) favored the 3.71 reference under default timings. Use alternate cadence as an opponent stress test and keep the standard benchmark. These figures estimate sensitivity to a local assumption. The official house controller and commit behind 4.10 remain unverified.
