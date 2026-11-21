# Offset aim for sideways motion before the gun fires

Tested `4880c655135b1104aef6899d0814cd1445c13146` against `cc762848`. It shifts the target by up to one meter according to current relative sideways motion before the expected first- or second-tick gun launch. It retains the existing weapon-priority and movement rules. In an archived proxy for 1,326 shots, mean lateral error fell from 1.008 m to 0.589 m, while errors exceeding 3 m went from 46 to 49.

| Simulated sample | Pairs | Placement points per game | Improved / tied / worse |
| --- | ---: | ---: | ---: |
| Public upgrades, 1000201–1000224 | 24 | +0.292 | 6 / 15 / 3 |
| Independent public upgrades, 1001101–1001116 | 16 | −0.188 | 3 / 12 / 1 |
| Independent hull growth and impact direction, 1001201–1001216 | 16 | −0.563 | 1 / 12 / 3 |
| Legacy four-mech, 1000301–1000306 on both maps | 48 | +0.021 | 1 / 47 / 0 |

The five earliest aim changes checked from wins and losses had equal first-second damage. Some later firing improved, including a fresh case with 126 more outgoing over three seconds that eventually lost seven places. Current relative velocity cannot establish the whole follow-up trajectory. All 25 tests and 300 starter-check observations passed.

Combat voted **reject** because both independent panels declined and the pooled campus change was −5 total. Survival and validation voted **revise** to seek a reliable hit-level condition before changing aim. An earlier timed clearance probe suppressed just one extra trigger across 109,190 archived decisions. That triggered shot actually hit for 91.8 damage in seed 990604. Keep the existing trigger and avoid generalizing the obstruction proxy from that probe.
