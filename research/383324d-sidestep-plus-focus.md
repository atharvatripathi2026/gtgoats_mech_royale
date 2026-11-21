# Projectile sidestep plus squad targeting

The two-parent candidate `383324dd95d9a7a9a625d930cfa4ef68ea288879` combined projectile sidestep `e0e641aeea2223f7a8dc6760188d4e2a939cd8eb` and squad focus `c1456b52088811a77a41473c50c4c70faa81d2e4`. Combat and validation voted **reject** for practice. Survival voted **revise** against squad focus and **reject** against projectile sidestep.

| Paired local panel | Compared with squad focus | Compared with projectile sidestep |
| --- | ---: | ---: |
| Campus squad, 24 pairs | +1.083 | −0.250 |
| Independent campus squad, 20 pairs | −0.600 | −0.300 |
| Four-mech, 64 pairs | +0.047 | +0.063 |

On independent seed 913305, the merge and standalone sidestep made the same first five sidesteps. At 7.7 seconds the merge turned to fire at a wounded rival farther away. The nearer rival disappeared from observation by 8.4 seconds, and the bot switched to its lone-pursuer maneuver. It took 1,685 damage by 100 seconds, versus 500 for sidestep alone, and fell from third to 11th locally. This is evidence for testing a short memory of a second visible threat. That test should preserve the existing retreat options and change only the lone-pursuer decision.

The exact merge passed 24 unit tests and all 300 official replay observations. The survival comparison launcher returned a nonzero exit status without an error message. The reviewer verified every expected episode record and shared simulator input hash before computing results. No approvals were recorded for the practice queue.
