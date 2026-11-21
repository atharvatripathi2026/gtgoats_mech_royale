# Combine gun timing and rear protection during reload

Tested exact two-parent merge `3579edd08c04f595df70618445fa6c329dac68db`. It retains the gun timing from `cc76284` and the rear guard from `a1ae1d7`. A focused fixture shows that the guard leaves a restored second-tick trigger and its commanded aim intact. The protection requires an active reload and no viable shot.

| Simulated comparison | Pairs | Placement points per game | Improved / tied / worse |
| --- | ---: | ---: | ---: |
| Vs trigger, public upgrades, 990001–990024 | 24 | 0.000 | 0 / 24 / 0 |
| Vs trigger, directional-impact holdout, 990701–990716 | 16 | +0.125 | 1 / 15 / 0 |
| Vs trigger, scaled-hull holdout, 990801–990816 | 16 | 0.000 | 0 / 16 / 0 |
| Vs trigger, legacy four-mech, 990101–990106 on both maps | 48 | 0.000 | 0 / 48 / 0 |
| Vs guard-only, common standard seeds 990001–990024 | 24 | −0.125 | 1 / 22 / 1 |
| Vs guard-only, common scaled seeds 990801–990816 | 16 | +0.313 | 3 / 12 / 1 |

In three windows, the added facing guard saved 22.5 HP with equal outgoing damage. Each tied on placement. The corrected-impact placement gain on seed 990715 had equal first-second damage. The larger change against guard alone on standard seed 990023 first altered a trigger only, with equal first-second damage and a four-place loss. All 26 tests and 300 starter-check observations passed.

Combat and validation voted **approve for practice** based on the reproduced armor effect, trigger precedence and no placement losses versus the trigger parent. Survival voted **revise** because the placement gain lacks direct attribution and the other comparable panels tied. The merge stays out of practice.

The exact guard-only transfer `58cba26aeb549f3e9bdb48f17a5de0a531333c1e` tied all 16 directional-impact pairs against `8b9f76d` on 990901–990916. It passed 24 unit tests and 300 starter-check observations. Combat, survival and validation each voted **reject** on the standalone candidate. It served as the comparator for isolating the trigger's contribution.
