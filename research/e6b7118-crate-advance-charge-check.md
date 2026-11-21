# Check actual laser charge before stepping toward a crate

Tested `e6b711864eb2b5cf79aa8a4ca28791cf17e896c6` against `8b9f76db264c8aa33e6c70b8ef67c741cb56f60d`. The [prior crate advance](73c1645-crate-reload-advance.md) now reads the documented numeric laser charge in the bot's own weapons. The new fixture checks that active charge stops the step even at an identical reported cooldown. All 24 tests and 300 starter-check observations passed.

| Simulated comparison | Pairs | Placement points per game | Improved / tied / worse |
| --- | ---: | ---: | ---: |
| Repeated standard 991501–991516 | 16 | +0.625 | 2 / 14 / 0 |
| Fresh standard 991801–991816 | 16 | 0.000 | 0 / 16 / 0 |
| Fresh scaled 991701–991716 | 16 | −0.125 | 0 / 15 / 1 |
| Four-mech 991201–991206 on both maps | 48 | 0.000 | 0 / 48 / 0 |

The repeated panel reproduced identical gains on the earlier seeds, verifying the charge check on those scenarios. It adds no independent gain. In scaled seed 991713, legs moved toward crate 1035 at 3.2 seconds while the gun still engaged mech 6 at 150 m. First-second damage was equal. The first cube and laser arrived 2.5 seconds later, and survival fell by 57.8 seconds. In the two motivating replays with earlier pickups, the combat selector was targeting the crate itself.

Combat voted **reject** for fresh non-replication and the scaled loss. Survival and validation voted **revise** based on the same counterexample and the observed difference in combat target. Retain the protocol-correct charge guard and require the combat selector's actual target to be the same crate before testing another movement change.
