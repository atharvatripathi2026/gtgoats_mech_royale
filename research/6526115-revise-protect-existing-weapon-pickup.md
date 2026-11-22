# Reach the selected weapon without displacing an existing pickup · revise

Exact `65261151c9a712b44a8ce8da67dc918c39682bbe` proposes an accessible point inside the pickup radius for a quiet, grounded bot with an empty slot and a blocked center approach. It collects mortar 8038 at 126.0s and gains five simulated placement points on stock and raw replays of 1071185. All 44 fresh placement pairs tie. The broader preliminary cube variant moves through a 2.84m raw gap in 1071181, below the four-cube hull's 3m radius. This exact version excludes cube movement and preserves that control.

A staged variant of the 125.8s replay adds lightning 8044 at 3.70m on the opposite side. The native pickup selector has already requested it. Native braking moves the actor to 3.966m and the actual collection succeeds. The fallback moves it to 4.056m and the actual collection fails. The game integrates movement before the pickup attempt. Survival, combat and validation revised their ballots after this counterexample.

The next exact variant yields to an already requested pickup. The first version passed 23 unit tests and the sandbox with 299 of 300 observations on time in its concurrent check. [Prior cube-detour review](d8b57b5-wall-checked-cube-detours.md)
