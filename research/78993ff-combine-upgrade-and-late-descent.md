# Gun throughput upgrades plus late-jet descent

The exact merge `78993ff9e4c515b3240860f83a18d7513ec50b24` has gameplay parents `8b9f76db264c8aa33e6c70b8ef67c741cb56f60d` and `c0727065234f3aa6f87f014e24a3c2c4ed5ac0f3`. The two runtime changes are the inherited healthy gun-throughput choice and the inherited late boost cutoff when no shot is possible. Upgrades can change survival or readiness before a late boost decision is reached.

| Fresh simulated comparison | Seed starts | Pairs | Placement points | Gains / losses |
| --- | --- | ---: | ---: | ---: |
| Standard, joint, faster joint against gun gear parent | 1026601, 1026701, 1026801 | 48 | 0 | 0 / 0 |
| Joint and faster joint against late-jet parent | 1026901, 1027001 | 32 | +16 | 5 / 2 |
| Standard against verified `03a8f93` | 1026601 | 16 | +5 | 3 / 0 |
| Four-mech against verified, generated and campus | 1027101 | 48 | 0 | 0 / 0 |

The standard comparisons reuse the same 16 candidate seeds. All 24 unit tests and 300 starter sandbox ticks passed, with p99 28.6 ms.

In fresh joint 1026703 the first change cut boost. Over the following six seconds incoming damage rose from 405 to 945 and outgoing fell from 860.47 to 183.6. Both won. Directed 1023905 matched the beneficial late-jet parent throughout, and 970414 matched the beneficial gear parent. Directed standard 1014214 also matched the gear parent throughout and scored eight fewer points than the other parent. Its first change picked a drum magazine over efficient jets, and it died before the verified late fight.

Fresh standard 1026604 updated the [earlier mobility screen](2026-11-21T055236Z-upgrade-mobility-screen.md). The drum replacing efficient jets also produced a three-point gain when the bot had used zero boost and zero evade decisions in the prior ten seconds. Fresh faster joint 1027013 replaced reactor with gun damage under the same recent zero-boost, zero-evade history and gained nine. The separate five-point loss from rejecting efficient jets occurred after 16% recent boost at full energy. Test a prospective route or recent mobility gate on new seeds and use these cases to verify that such a guard preserves both good picks.

## Actual Sol verdicts for the exact commit

- Survival, revise. The fresh combination provided no placement gain over gear, and the jet change worsened the first six seconds of a tied win. The early mobility trade can foreclose the late policy.
- Combat, approve for practice. The real parents compose cleanly. The gains over late jet and verified, no placement losses versus gear, and exact positive late-jet replay support a practice attempt despite mixed local tradeoffs.
- Validation, revise. The improvement inherits the gear policy. The direct marginal jet comparison has only placement ties and at least one marked trade regression. Measure a more selective mobility or descent gate.
