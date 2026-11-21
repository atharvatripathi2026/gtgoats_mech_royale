# Combine crossing-shot sidestep with second-tick firing

Tested true merge `d656cb8460565dbeadf62b5e75c7572333d1d7fd`, with exact Git parents `cc7628485b7b5ea5b53f51af18baec5e624bd86a` and `e0e641aeea2223f7a8dc6760188d4e2a939cd8eb`. The merge preserves both mechanics and leaves the first parent's other gameplay files in place.

| Simulated comparison | Pairs | Placement points per game | Improved / tied / worse |
| --- | ---: | ---: | ---: |
| Vs trigger, standard public, 1001401–1001416 | 16 | −0.063 | 4 / 7 / 5 |
| Vs trigger, standard confirmation, 1001601–1001624 | 24 | −0.375 | 6 / 9 / 9 |
| Vs trigger, joint hull and impact, 1001301–1001316 | 16 | +0.875 | 5 / 4 / 7 |
| Vs trigger, joint confirmation, 1001701–1001724 | 24 | +1.000 | 6 / 14 / 4 |
| Vs sidestep, same joint seeds 1001301–1001316 | 16 | +1.250 | 5 / 9 / 2 |
| Vs trigger, legacy four-mech, 1001501–1001506 across both maps | 48 | +0.208 | 6 / 41 / 1 |

In joint seed 1001307, the largest placement gain began with a deflection that took 67.5 more damage in the first second. In 1001316 the largest placement loss followed an avoided 67.5 damage and 243 less outgoing over three seconds. Smaller gains sometimes came with direct damage savings. Forty standard pairs lost ten total placement points, while the forty joint pairs gained 38. The difference between model settings is repeatable on the chosen samples. All 25 unit tests and 300 starter-check observations passed.

All three Sol reviewers voted **revise** after the confirmation panels. Combat revised its initial approval after seeing the second standard loss. Survival cited the real but mixed short-window avoidance effects. Validation cited differing outcome directions under plausible arena assumptions and the opposing signs of immediate damage in the largest placement changes. Keep the exact merge out of practice and profile abrupt reversals using the actual steered trajectory rather than relying on final placement for mechanism attribution.

## Isolate the effect of the model

The same 16 seeds 1001301–1001316 ran against the trigger parent under four arena settings.

| Simulated setting | Placement points per game | Improved / tied / worse |
| --- | ---: | ---: |
| Original hull and bearing | -0.688 | 3 / 8 / 5 |
| Scaled hull alone | -1.062 | 0 / 11 / 5 |
| Impact bearing alone | +0.125 | 5 / 6 / 5 |
| Both rules | +0.875 | 5 / 4 / 7 |

The large favorable change appeared only when both simulator choices were enabled on this matched panel. That interaction does not identify the arena setting closest to the official match.
