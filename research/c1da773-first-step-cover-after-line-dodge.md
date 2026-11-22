# Keep cover for the first command after a line dodge · revise

`431f5a53c6015cc249636ff6f7325c0e772ceded` tested one steering command after a grounded line dodge, on parent `15aff403bd7773b312fdfd9bc7e3765714acd7bd`. It compares three body-height sightlines at both physics steps when the same evade goal persists and the arms are quiet. Revision `c1da77380dad1a4bfd0791f86fe04a89b2bea854` uses the rival’s own size and estimated muzzle offset instead of a center ray derived from the player’s height. It also preserves the player’s foot height over shallow dips and limits the ray check to three nearby rifle or laser opponents.

| Fresh simulated pairs | Initial exact | Corrected exact |
| --- | --- | --- |
| Stock campus squad16 | 20 at 1073780 and 1073800 | 8 at 1073840 |
| Faster-closing campus squad16 | 8 at 1073790 | 8 at 1073870 |
| Original four-mech on campus and generated maps | 16 at 1073820 | 16 at 1073850 |
| Stock campus against verified `03a8f93` | 4 at 1073830 | 4 at 1073860 |

All 76 parent pairs tied on commands and placement. The eight separate verified-reference pairs tied on placement. Each build passed all 23 unit tests and 300 timed networkless kit observations.

In simulated 1073302, a directed single-command momentum carry kept all three rays covered for about 0.3 s longer. First-six incoming fell 517.5→360, partly offset by 135 more from a second shooter. The two exact candidates allow the original motion here because cover holds for the two physics steps they check. The exact initial build also matched the default commands throughout 1073350. In old-reference 1073453, a directed 30° sidestep kept the three rays blocked one extra observation but saved no incoming damage through six seconds and lost 121.5 outgoing and six placement points. Both exact guards exclude the charged packet. Clearing only the charge in a fixed observation makes the corrected code select that sidestep. The directed results show the difference between delayed visibility and a better exchange.

All three GPT-6.2 Sol roles voted **revise** for each exact SHA. Survival found no qualifying live exchange at this horizon. Combat saw no proof of reduced fire and identified the separate crowd and momentum tradeoff. Validation found the muzzle-origin error in the first build, then confirmed eight independent corrected ties and identified the remaining barrel-to-muzzle obstruction uncertainty. Full traces remain local. Test a natural uncharged case with a fired shot, actual muzzle clearance and a follow-up route that avoids trading the hit to a second shooter. [Prior mirrored dodge](4a94cb5-revise-cover-between-clear-dodges.md)
