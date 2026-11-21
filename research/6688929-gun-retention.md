# Gun retention with a tracked opponent

All three GPT-6.2 Sol reviewers rejected `6688929337903c7df5414c07d37f9f2547d86737` for practice. It withheld reloads while a previously engaged opponent was still reported by sensors, when only the gun was available and several rounds remained. Its parent is squad focus `c1456b52088811a77a41473c50c4c70faa81d2e4`.

| Review | Paired local games | Mean placement change |
| --- | ---: | ---: |
| Combat and equipment | 36 squad | +0.083 |
| Survival and positioning | 30 squad | −0.467 |
| Opponent modeling and validation | 48 squad | 0.000 |
| Four-mech regression check | 96 | −0.031 |

In the sole improved four-mech outcome, the remaining ammunition went to the same opponent when it came back. In the three regressions the ammunition went to a crate, a drone or a different opponent before a later engagement. The new rule corrected the [previous revision's recontact failure](64dc809-reload-timing.md) on seed 511911. The independent 48-game panel tied on all placements while average damage dealt fell by 46.6 per game. Sensor memory alone provided weak evidence of imminent recontact.

All 24 unit tests passed and 300 of 300 official replay actions arrived within budget. The holdout comparisons are local simulation evidence. Keep the parent's reload timing for practice and test how the bot chooses weapons for incidental targets separately.
