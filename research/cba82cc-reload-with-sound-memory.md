# Remember nearby combat sounds during a quiet reload

`cba82cca38cc2398a661d1eb1d2f0756f7042848` revises `bbf2ac92c0e17740b6b146041655f96991714bac` and compares primarily with `cc7628485b7b5ea5b53f51af18baec5e624bd86a`. It retains the latest nearby combat sound for one second using the event age. It keeps the other quiet reload conditions. The [earlier top-off](bbf2ac9-quiet-gun-topoff.md) had been relying on current observation sounds only.

| Fresh simulated panel | Seed start | Pairs | Placement-point change | Improved / tied / regressed |
|---|---:|---:|---:|---:|
| Standard campus | 1015001 | 16 | −1 | 1 / 13 / 2 |
| Independent standard campus | 1015301 | 16 | +2 | 1 / 15 / 0 |
| Joint hull and impact campus | 1015201 | 16 | 0 | 0 / 16 / 0 |
| Four-mech | 1015101 | 48 | 0 | 0 / 48 / 0 |

All 25 units and 300 starter observations passed. Sandbox p99 was 3.7 ms. Fixed replay blocks the top-off at 298.2 s in 990605 after hearing a mid-distance gun at 298.1, and preserves the quiet 1013811 reload at 70.0 s. The prior 31 fresh top-offs still satisfy the sound check on their recorded observations. A direct-parent closed-loop replay of 990605 ties with all 3,528 actions identical because its earlier reload changes whether the archived opportunity is reached.

In fresh 1015304 the extra rounds increased one-second damage from 94.5 to 189 against the same opponent during the baseline's reload, and gained two placement points. In fresh 1015012 the opponent returned without a preceding combat sound. The extra reload delayed the first gun trigger from 111.4 to 112.7 s and forfeited the incumbent's early 89.1 HP hit. That run lost one placement point. In 1015005 the first recontact trade was identical, the new variant dealt an extra 97.2 gun damage in a later window, and eventual placement fell seven points.

- Combat voted **approve for practice** because the sound hazard was fixed and the archive plus independent test showed usable extra ammunition at recontact.
- Survival voted **reject for practice** because the new no-sound recontact reproduced the firing risk and fresh placement was close to flat.
- Validation voted **revise** because the verified recent-sound correction still leaves unheralded contact unsafe during the reload.

The queue received no candidate. A further test should use geometry and the remaining reload time to admit a protected window, preserving the extra-round fixtures and excluding the 1015012 recontact.
