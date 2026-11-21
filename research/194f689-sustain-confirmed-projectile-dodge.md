# Continue a confirmed dodge through a follow-up round

`194f689dfa61d228dec51b5651ee3c86b4afa01b` revises direct parent `b9eb188b86e6854b60a99449c1e086bd7da4745e` and was primarily tested against effective baseline `cc7628485b7b5ea5b53f51af18baec5e624bd86a`. It extends the initial flank projection to 0.30 seconds. It can then retain the emitted move if a new, parallel player-gun projectile is consistent with the same uniquely aligned visible shooter. The follow-up checks safe ground and circle margin and protects the already computed aim, firing and boost commands. Projectile owner is inferred from position and velocity.

| Fresh simulated panel | Seed start | Pairs | Placement-point change | Improved / tied / regressed |
|---|---:|---:|---:|---:|
| Standard campus vs cc76284 | 1013601 | 24 | 0 | 0 / 24 / 0 |
| Independent standard vs cc76284 | 1014501 | 16 | +5 | 1 / 15 / 0 |
| Joint hull and impact vs cc76284 | 1014601 | 16 | 0 | 0 / 16 / 0 |
| Independent standard vs b9eb188 | 1014701 | 16 | 0 | 0 / 16 / 0 |
| Four-mech vs cc76284 | 1013701 | 48 | 0 | 0 / 48 / 0 |

All 26 tests and 300 starter observations passed. Sandbox p99 was 29.0 ms. In known seed 1012422 the variant held the dodge at 57.3 and 57.4 seconds. Both #10079 and the newer #10081 passed without hitting. The two parents each took 45 damage and all three dealt 641.48 over three seconds to the same enemy. Placement points were 12 for cc76284, 7 for b9eb188 and 8 for the new variant. In 1012705 the new policy reproduced every cc76284 action and restored its ten points. [Earlier guard and regressions](b9eb188-player-projectile-finisher.md)

The fresh win in 1014504 saved 41.4 damage at unchanged 230.4 outgoing over the next second. Direct-parent replay shows the same emitted actions and placement, so that gain belongs to the inherited initial guard. The new continuation never activated in the 72 fresh campus traces. A separate 56-match screen seeded from native rather than overridden line dodges found a single eligible strong reversal, with no newly visible gun round.

- Combat voted **approve for practice**, citing the causal avoidance with the same weapons and no fresh placement loss.
- Survival voted **revise** because the continuation never fired in fresh simulations, and the known placement loss only partly recovered.
- Validation voted **revise** because the follow-up repaired a proven hit without demonstrating additional fresh value. Shooter attribution and short gaps in visible rounds remain open.

The queue received no candidate for this behavior. Retain the two closed-loop fixtures for future changes to dodge persistence.
