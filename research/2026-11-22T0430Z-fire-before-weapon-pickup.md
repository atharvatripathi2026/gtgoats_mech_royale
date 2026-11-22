# Test firing before weapon pickup · 04:30 UTC

Evaluator-only `d3c9e5b87c33c5cc14d6f3355cdd931baede62c9` runs weapon pickup after that actor's firing. Cube collection, offers, movement and projectile stepping retain the stock ordering. It compares exact `5f0ace9` and `c022067`. The kit does not specify the live engine's pickup versus fire order.

In unstaged 1070726 both fire and hit with the mortar for 562.04. The earlier parent equips laser 10015 at 121.1s while the queued deferral equips it at 121.2s. First-six totals are 1,244.24 outgoing and zero incoming in both arms. Both score 15, survive 370s and get four kills. All eight fresh campus pairs (1072830–37) match every command and placement. This isolates the causal benefit in stock equip-first timing. The live order remains unverified. [Stock review](5f0ace9-mortar-before-laser.md)
