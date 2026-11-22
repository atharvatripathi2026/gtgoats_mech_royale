# Retain rifle aim while dodging a wounded drone

Practice ledger position 107 records exact `9c5f89bd2e77b8049f83a6102ee875998c1f220d` from `2e2436e4d1ddda95aac8a86c8a18027e276da03c`. Survival, combat, and validation each approved this SHA. The change holds existing rifle aim during an NPC-only line dodge if a recent confirmed hit wounded the sole visible opponent and the current aim faces every visible round. The native rifle brace keeps priority.

In simulated stock squad seed 1077443, only aim changes at 115.7 s. The two eventual rifle hits on NPC 104 land at 116.0 and 116.2 s instead of 116.2 and 116.4 s. First-six-second damage remains 111.6 outgoing and 25 incoming. Both pickups occur at the same times and the score stays at eight points. Lifetime rises 306.75→319.05 s while kills fall 7→5. Under the independent interpolated-terrain evaluator, the fire command advances by one 0.1 s observation and the actual hit stays in the same observation. Trade, loot, lifetime, and placement tie there.

All 28 fresh parent pairs match commands and placement across 12 stock squad seeds 1077420–31 and 16 original four-mech pursuit and crossfire pairs on campus and generated maps at seeds 1077400–03. All 23 starter-kit tests and 300 timed sandbox replies passed. The separate four-seed comparison to the verified 3.71 build averages +1.50 on placement and is entirely explained by the existing parent at 1077443.

[Previous rifle reserve during a drone dodge](740aa2f-reserve-rifle-through-npc-dodge.md)
