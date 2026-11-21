# Transfer the gun upgrade scorer onto the gun clearance family

Tested `1e12464feff23f54db4c048d3dfa6d7cf0b54a0b`. It combines the published intercept and spread checks from `88460d6` with the sustained upgrade scorer from `367287e`. The latter is the gameplay donor; the exact Git parent is `88460d6`.

| Simulated comparison | Pairs | Placement points per game | Improved / tied / worse |
| --- | ---: | ---: | ---: |
| Vs clearance, public-upgrade campus 966401–966416 | 16 | 0.000 | 1 / 14 / 1 |
| Vs throughput, same campus seeds | 16 | 0.000 | 5 / 8 / 3 |
| Vs clearance, legacy four-mech 966501–966506 on both maps | 48 | 0.000 | 0 / 48 / 0 |

The source and tests retained both behaviors. Relative to throughput on the same campus seeds, the combination averaged 9.72 seconds less survival and 34.38 HP more zone damage, with equal placement. This comparison also changes the underlying movement and combat family. The clearance comparison isolates the upgrade change.

Twenty-five unit tests and all 300 starter-check observations passed. All three Sol reviewers voted **reject**. Combat saw no incremental placement improvement over the individual versions. Survival cited the offsetting placement changes, shorter survival and greater zone exposure. Validation noted that both comparisons used the same campus seeds and found no evidence for advancing the combination. Review exact combinations against both active parents before spending a practice slot.
