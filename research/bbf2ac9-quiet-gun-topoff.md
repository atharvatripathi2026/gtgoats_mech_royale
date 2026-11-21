# Refill a nearly full gun after a quiet interval

`bbf2ac92c0e17740b6b146041655f96991714bac` changes high-ammo reloads on `cc7628485b7b5ea5b53f51af18baec5e624bd86a`. It tops off at least two missing rounds after 2.5 seconds without a tracked mech, target, or bearing-carrying hit. It skips low health, exposure, planned items and current nearby combat sounds and keeps the existing empty and below-80% reload rules.

| Fresh simulated panel | Seed start | Pairs | Placement-point change | Improved / tied / regressed |
|---|---:|---:|---:|---:|
| Standard campus | 1013801 | 24 | +13 | 4 / 18 / 2 |
| Independent standard campus | 1014801 | 16 | +4 | 3 / 13 / 0 |
| Joint hull and impact campus | 1014901 | 16 | −3 | 0 / 15 / 1 |
| Four-mech | 1013901 | 48 | 0 | 0 / 48 / 0 |

All 25 tests and 300 starter observations passed on the sandbox recheck. At the same recontact in 1013811 the variant had 12 instead of 10 rounds, delayed its in-fight reload from 113.4 to 113.9 seconds, and delivered an additional 156.6 outgoing damage with equal incoming across the first three seconds of contact. Several independent standard wins also showed extra rounds at native empty-magazine frames, although advantage varies with the alignment of strike and reload windows. Controlled archival replays 990622 and 990611 placed one higher and two lower respectively.

The original sound test reads only the current observation. In archived 990605 the bot hears a mid-distance gun at 298.1 s, then starts the new top-off a tenth of a second later when the next buffer is empty. The foe reappears at 298.6 and the incumbent fires at 298.8, before the added reload could finish. The 31 fresh top-offs had zero observed nearby combat sounds in the preceding second, so this hazard was absent from the fresh samples. Another archived state re-acquires a foe without prior sound, which remains a separate risk.

- Combat voted **approve for practice** because the repeated reserve-ammunition gains and overall +14 across 56 campus pairs justify an official experiment.
- Survival voted **revise** because the quiet gate can admit the observed recent-gunshot hazard and the joint panel lost points.
- Validation voted **revise** because the direct reserve benefit is promising, but retaining nearby gun sound across observations fixes a demonstrated unsafe interval.

The queue received no candidate for this exact behavior. Preserve the positive reload fixture and re-screen sound memory on fresh pairs.
