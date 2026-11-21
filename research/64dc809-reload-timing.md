# Reload timing after losing sight of an opponent

All three agents voted **revise** on `64dc809a5accfa5ab0fa007b7b7f8a7dfeb5fe74`, a local child of the approved squad-focus policy. The change delays a voluntary reload after brief contact loss if the gun still has usable ammunition.

| Review | Fresh paired squad games | Mean local placement change |
| --- | ---: | ---: |
| Combat and equipment | 48 | +0.729 |
| Survival and positioning | 24 | −0.333 |
| Opponent modeling and validation | 48 | −0.271 |
| Additional traced check | 8 | −0.875 |

The four-mech holdout tied across 160 pairs. In eight diagnostic squad traces the change reduced high-ammunition reloads interrupted by contact, but increased exposure while reloading an empty magazine. On seed 511911 the bot waited 0.8 seconds to start a reload with six rounds left. When the opponent returned, the parent got four more shots off and dealt 146 more damage in that firing window. The later game outcome cannot be attributed to that window alone.

The combat reviewer will test whether the last opponent could return quickly enough to interrupt a reload. Preserve the existing policy when the evidence for changing reload timing is weak. These are local simulation results. The submitted queue was unchanged by this trial.
