# Defer high-ammo reload when leaving an occluded hold

`be2c1f38d94ee8b717ab4f236e144b09d7791c03` revises `ddf00bcb4478b8079766f09050fa4be93d2ba7db`. It applies the forward-visibility veto only when leaving a genuine 0.5-second stationary hold. A veto latches for the weapon's reload time so a single clear subsequent observation does not restart the reload. Existing low-ammo reloads are preserved. The tests use `cba82cca38cc2398a661d1eb1d2f0756f7042848` for the pre-veto behavior and `cc7628485b7b5ea5b53f51af18baec5e624bd86a` for the effective no-top-off baseline. [Broad-veto experiment](ddf00bc-forward-visibility-topoff.md)

| Fresh simulated panel | Baseline | Seed start | Pairs | Placement-point change | Improved / tied / regressed |
|---|---|---:|---:|---:|---|
| Standard campus | cba82cc | 1016701 | 16 | 0 | 0 / 16 / 0 |
| Independent standard | cc76284 | 1016901 | 16 | 0 | 0 / 16 / 0 |
| Joint hull and impact | cc76284 | 1017001 | 16 | +5 | 4 / 11 / 1 |
| Four-mech | cc76284 | 1016801 | 48 | 0 | 0 / 48 / 0 |

A matched rerun of the same 16 joint seeds against cba82cc tied every placement. Fifteen action streams were identical. In the remaining game, the reload was deferred with no change in placement, survival, or dealt and received damage. The +5 relative to cc76284 was already present in the prior reload policy.

All 26 units and 300 starter observations passed, with sandbox p99 of 21.3 ms. The exact closed-loop 1015012 match restores the 111.4-second gun trigger and the early 89.1 HP hit, recovering one placement point. Fixed replays preserve both safe continuous-motion top-offs that the broad veto removed. The closed-loop replay 1015414 also restores the baseline's 15 placement points.

In fresh 1017002 the variant topped off while already moving and an opponent reappeared within 0.5 seconds. Its first gun trigger moved from 129.5 to 131.5 and first-three-second damage fell from 513.36 to 64.17 at equal incoming. It later dealt 192.51 additional gun damage while the baseline was empty and finished two points higher. The held-out 1017013 gained two usable rounds and increased one-second damage from 48.6 to 145.8 versus the same target and eventual placement by one point. The quiet reload can trade early readiness for later reserve, even after the departure correction.

- Combat voted **approve for practice** because the known hazard was corrected and the joint holdout supported reserve ammunition value.
- Survival voted **revise** because the new policy showed no incremental gain over the sound-memory baseline and repeated the readiness risk during continuous travel.
- Validation voted **revise** because the fresh two-second delay shows that a hold departure alone does not capture the early-contact risk.

The queue received no candidate for this behavior.
