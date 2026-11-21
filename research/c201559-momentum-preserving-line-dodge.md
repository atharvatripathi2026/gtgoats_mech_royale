# Momentum during an existing line dodge

The three reviewers rejected `c201559d8984a9f437f4fb6fcc8748fc8bb6012c` for practice. Its gameplay parent is `57b8da24d01a8315e94faa21cb6e0c811cf7ea66`. The policy uses measured velocity on grounded reversals and substitutes a continuation only if the short acceleration forecast clears visible direct shots and legal terrain. The existing dodge marker, aim, weapons, boosts and logging are preserved.

| Simulated panel | Seed start | Pairs | Placement-point change | Improved / tied / regressed |
|---|---:|---:|---:|---:|
| Standard campus | 1010201 | 24 | −14 | 0 / 22 / 2 |
| Independent standard campus | 1011001 | 16 | 0 | 0 / 16 / 0 |
| Joint hull and impact campus | 1011101 | 16 | −1 | 1 / 13 / 2 |
| Four-mech | 1010301 | 48 | −3 | 1 / 45 / 2 |

All 26 units and 300 starter observations passed. The 300-tick sandbox p99 was 39.8 ms under load. Controlled replays saved 37.5, 37.5 and 25 HP from the first NPC shot in three games, with placement-point changes of −1, +2 and −3. The worst fresh result, seed 1010216, improved the first-three-second damage trade after the decision at 45.3 s, then altered the farm route and died 231.35 s earlier. That game lost 13 placement points. The archived trigger check activated eight times across 811 native line-dodge frames in 56 matches. A new laser charge can change speed during the prediction window.

- Survival voted **reject for practice** because local HP saves accompanied a placement loss across three panels. An additional same-heading brake check at four speed scales still intersected the trigger in all ten examined exposures.
- Combat voted **reject for practice** because both independent and owner panels supplied no placement upside and an initiating laser charge can invalidate the predicted movement.
- Validation voted **reject for practice** because the largest loss followed an apparently favorable NPC trade. Compare native and one-observation alternatives against the same tracked player-projectile ID while preserving aim and the planned route. Use 1010216 as an NPC exclusion fixture.

The queue received no candidate for this behavior.
