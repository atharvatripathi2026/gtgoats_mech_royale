# Second-tick gun trigger on the sidestep and magazine lineage

All three reviewers voted revise on `bacc6b112855f40a6702b69556ddad935d1c6cc3`. The two verified parents are `367287e08745649c728a9cbee2ad2311ac781156` and `cc7628485b7b5ea5b53f51af18baec5e624bd86a`. The merge applies the exact second-tick gun trigger from the latter and retains the former's remaining gameplay. At an unchanged aim, an already selected gun can hold fire when its cooldown ends on the second physics tick and the muzzle will align by then. It preserves ordinary gun actions and existing sidearm selection.

| Simulated panel vs. 367287e | Seed start | Pairs | Placement-point change | Improved / tied / regressed |
|---|---:|---:|---:|---:|
| Standard campus | 1010001 | 24 | +9 | 2 / 22 / 0 |
| Independent standard campus | 1010601 | 16 | 0 | 0 / 16 / 0 |
| Standard confirmation | 1011301 | 24 | +4 | 2 / 21 / 1 |
| Joint hull and impact campus | 1010701 | 16 | −2 | 1 / 13 / 2 |
| Joint confirmation | 1011201 | 24 | −5 | 0 / 22 / 2 |
| Four-mech | 1010101 | 48 | 0 | 0 / 48 / 0 |

Against the other parent, `cc76284`, the merge lost four points on the same 16 joint seeds, with four wins and four losses. This comparison includes separate targeting and stance policies. All 25 units and 300 starter observations passed, with p99 of 1.7 ms. Replaying 179,312 archived observations added 104 gun triggers in 23 of 64 matches. Four mismatches were already present when reconstructing the parent; the same-input trigger check isolated the intended gun additions.

Each of the five confirmation matches with changed placements started with equal first-second damage. In the next three seconds, the new policy dealt 438 more in standard seed 1011301 and 471.8 more in joint seed 1011201 with the same incoming damage. Their eventual placements moved in opposite directions. The tied owner seed 1010023 dealt 55.8 more in the first second with equal incoming damage.

- Survival voted **revise** because the confirmation's placement gains and losses had equal first-second trades, and the independent joint penalty repeated.
- Combat voted **revise** because the timing mechanic supplied a real extra hit, but two joint panels favored the parent and four-mech placements all tied.
- Validation voted **revise** because recovered early damage helped an eventual winner and an eventual loser, and the joint placement decrease repeated.

Retain the already queued parent variants. Pause timing-only transfers while examining whether a different weapon choice can improve repeatable short-window trades. The queue received no candidate for this behavior.
