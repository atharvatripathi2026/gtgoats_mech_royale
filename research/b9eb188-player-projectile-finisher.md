# Preserve a dodge when a finishing flank crosses a player shot

`b9eb188b86e6854b60a99449c1e086bd7da4745e` revises the [earlier finisher guard](873281e-preserve-imminent-line-dodge.md) on `cc7628485b7b5ea5b53f51af18baec5e624bd86a`. It forecasts two observations of clear grounded steering. The guard keeps the native dodge only when both tested flank continuations intersect the same visible gun projectile and both native continuations clear direct shots. It skips visible mortar, active laser charge, and modeled navigation recovery. An uncharged laser first triggered on the same action can still affect the forecast.

| Fresh simulated panel | Seed start | Pairs | Placement-point change | Improved / tied / regressed |
|---|---:|---:|---:|---:|
| Standard campus | 1012401 | 24 | −5 | 0 / 23 / 1 |
| Independent standard campus | 1012601 | 16 | 0 | 0 / 16 / 0 |
| Joint hull and impact campus | 1012701 | 16 | −1 | 0 / 15 / 1 |
| Four-mech | 1012501 | 48 | 0 | 0 / 48 / 0 |

All 25 unit tests and 300 starter observations passed. Sandbox p99 was 27.9 ms. A fixed replay of 56 games identified four guarded windows. Three changed the emitted move; the fourth entered navigator recovery. There was no laser in any of those four. A known bad case, 1010402, replayed with identical actions and outcome. Standard archived games 1010404 and 1010811 avoided 45 and 90 incoming damage over three seconds with identical outgoing damage and gained six placement points each. But the same 1010404 decision in the joint model still avoided 45 and dealt 167.8 in the first second and finished with 12 fewer placement points. This was the only placement change across 12 archived joint pairs.

In fresh joint seed 1012712 the change avoided 45 damage with equal outgoing over three seconds and both bots won. In joint 1012705 the original projectile #10037 still hit for 45 one observation later. In owner 1012422 it avoided #10079, but a new round #10081 entered observation one decision later and hit for the same damage. Both bots dealt 641.5 and took 45 over three seconds. The change lost five placement points there.

- Survival voted **reject for practice** because fresh placement gave no gains despite multiple clear immediate saves.
- Combat voted **reject for practice** because one fresh hit was postponed only and the tested guard still approximates newly initiated charge.
- Validation voted **revise** because direct projectile tracking confirmed real saves but also found a follow-up round that erased the immediate benefit.

A 0.30-second fixed-input projection excludes 1012705 and preserves the demonstrated saves. It still admits 1012422 because the second round was outside the initial observation. Revisit after a targeted plan can maintain the dodge against a follow-up without replacing the route. The queue received no candidate for this behavior.
