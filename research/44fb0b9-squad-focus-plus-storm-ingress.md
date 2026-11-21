# Combine squad focus and storm ingress

Exact `44fb0b97bb29db419dcc3b3984926def927fb04a` has actual approved parents `c1456b52088811a77a41473c50c4c70faa81d2e4` and `fe63d42d2743848f7933309c833577e5b204ba35`. The storm override still checks whether loadout intends to fire, so a focus target change can affect when the movement policy is eligible.

| Fresh comparator | Seeds | Pairs | Placement points |
| --- | --- | ---: | ---: |
| Focus parent, standard and joint | 1032801, 1032901 | 40 | +1 |
| Storm parent, standard | 1032801 | 24 | +11 |
| Storm parent, faster joint | 1033001 | 16 | −2 |
| Verified, standard | 1032801 | 24 | +12 |
| Verified, four-mech | 1033101 | 48 | +1 |

The three standard contrasts use the same 24 candidate seeds. Exact tests and all 300 starter sandbox observations passed. Directed 1027423 retained the storm route's earlier re-entry, reducing first-three-second storm damage from 300 to 90 and scoring 15 points against eight for focus alone. In fresh standard 1032811 adding storm to exact focus cut the first three seconds of storm damage from 295 to 40, with one higher placement. Late incoming damage increased by 394.8 in the same match.

Against storm in standard 1032803, focus switched damage from target 1 to target 14 at 75.6 s, with equal movement. One-second outgoing fell by 59.4, then total outgoing and incoming through six seconds tied. Final placement points fell from 12 to 5. Faster joint 1033011 fell by ten points against storm after a focus target switch, without different early total damage. The early changes demonstrate a target allocation tradeoff and the final placements encompass later fights.

## Actual Sol votes for the exact commit

- Survival, revise. One incremental gain over focus in 40 matches and mixed results across arena models. Joint or faster holdouts should show incremental advantage before combining.
- Combat, approve for practice. The movement-only first gain against exact focus demonstrates successful composition and the standard gains justify a practice attempt, with the faster target-switch loss a material risk.
- Validation, revise. Improvement over verified largely comes from the focus parent. The faster loss and single incremental gain do not justify practice for this merge yet.

[Storm evidence](fe63d42-earlier-legal-storm-ingress.md)
