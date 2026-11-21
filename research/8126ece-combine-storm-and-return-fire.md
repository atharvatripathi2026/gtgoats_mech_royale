# Combine storm ground ingress and late airborne return fire

Exact `8126ece8e9c29ecd6d1883e37a226955b26e6929` has approved parents `fe63d42d2743848f7933309c833577e5b204ba35` and `c0727065234f3aa6f87f014e24a3c2c4ed5ac0f3`. It uses both native methods after loadout. The storm route needs grounded play outside the circle and the return-fire jet cutoff needs air time inside, so they cannot change the same action. They can change the same match.

| Fresh simulated control | Seed starts | Pairs | Placement points |
| --- | --- | ---: | ---: |
| Storm parent, standard and joint | 1030501, 1030601 | 32 | −1 |
| Jet parent, standard and faster joint | 1030501, 1030701 | 32 | 0 |
| Verified parent, standard | 1030501 | 16 | 0 |
| Verified four-mech, generated and campus | 1030801 | 48 | 0 |

The three standard contrasts share the same 16 candidate seeds. The exact assembly passed 24 unit tests and 300 starter observations.

Directed 1027423 and 1023905 kept the complete winning paths of their respective parents. In directed joint 1028202 both methods activated. The merged run dealt 1260 more damage than storm alone and took 184 more from the storm, with equal total incoming and placement. In 1025110 it survived 2.6 s longer while taking 165.6 more damage, with equal storm damage and placement.

The only fresh placement change was joint 1030611. The storm policy did not activate. The jet command turned boost off at 331.4 s, bringing 63 damage at equal incoming in three seconds and 630 outgoing with 90 additional incoming by six seconds. The merge ended second with 770 less outgoing and 70 more incoming, while the storm parent won. The contemporary [final duel screen](2026-11-21T062430Z-final-duel-descent-screen.md) records the narrow follow-up.

## Actual Sol verdicts for the exact commit

- Survival, reject for practice. The merge retained both favorable replays but added a fresh loss and a measurable storm versus fire tradeoff.
- Combat, reject for practice. An earlier shot in the regression did not translate to later combat, and the exact combination gained no fresh placements.
- Validation, revise. Direct paired comparisons against both parents lack an incremental gain. Review the late-duel distinction before another merge.
