# Combine storm ingress with final-duel-guarded descent

Exact `084ef5f05dbfcd078a2cac94c80333bf6ebee8d0` has actual approved parents `fe63d42d2743848f7933309c833577e5b204ba35` and `1007d94d9de578353be95597a11a7ba6049e81be`. Its only runtime change relative to the previously tested merge is the final-duel guard. Movement remains the grounded storm policy outside the circle, and optional descent is airborne inside earlier in a fight.

| Fresh simulated comparator | Seed starts | Pairs | Placement points |
| --- | --- | ---: | ---: |
| Storm parent, standard and joint | 1034901, 1035001 | 40 | −1 |
| Guarded jet parent, standard and faster joint | 1034901, 1035101 | 40 | 0 |
| Verified, standard | 1034901 | 24 | −1 |
| Verified four-mech | 1035201 | 48 | 0 |

The three standard contrasts use the same 24 candidate seeds. All 24 units and 300 starter sandbox ticks passed.

The merge reproduced every action of the winning correction at 1030611 and both positive parent trajectories at 1027423 and 1023905. It also reproduced the old interaction at 1028202, gaining 1260 outgoing damage and taking 184 more storm damage at tied placement. In fresh standard 1034922 the first change at 299.1 s was the inherited boost cutoff at the same selected target. Placement fell one point versus storm and verified, and the exact guarded-jet parent matched that outcome. In fresh faster joint 1035112 the move-only storm response cut three-second incoming from 480 to 96, all storm damage in that window. By six seconds outgoing fell from 922.89 to zero. In the complete tied match the bot took 552 more damage from the storm and 1225.62 more incoming overall while surviving 30.55 seconds longer.

## Actual Sol votes for the exact commit

- Survival, reject. The old failure is fixed and each parent's known gain is preserved. Fresh placements provide no incremental benefit and the faster replay has a concrete exposure trade.
- Combat, revise. The final-duel correction works, but no fresh incremental placement gain and the later storm and hostile exposure keep the merge from practice.
- Validation, reject. The tested exact parents already capture the directed positives, and the new controls show an inherited placement loss and the renewed storm trade.

[Original merge evidence](8126ece-combine-storm-and-return-fire.md) · [Final-duel correction](1007d94-final-duel-jet-veto.md)
