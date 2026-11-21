# Return fire at the tracked rival under live gun pressure

`e3184ebc9732c1f3492c9dfeee231a0c398618f7` descends from verified `03a8f93fb36afa5db4a08f211d1d1aa6dcbcae8e`. During an evade with a native track-only target, it can allow the loaded and aligned gun to fire if a visible approaching projectile can be traced back toward that same rival and a shot ray is clear. It preserves the selected target, legs and other weapon eligibility. Shooter identity is inferred from geometry.

| Fresh simulated panel | Seed start | Pairs | Placement change | Improved / tied / regressed |
|---|---:|---:|---:|---:|
| Standard campus | 1019801 | 24 | 0 | 0 / 24 / 0 |
| Independent standard campus | 1020301 | 16 | −7 | 0 / 14 / 2 |
| Joint hull and impact | 1020401 | 16 | −1 | 0 / 15 / 1 |
| Four-mech | 1019901 | 48 | 0 | 0 / 48 / 0 |

All 23 unit tests and 300 starter observations passed, with sandbox p99 of 26.9 ms. Fixed replay on 64 matches found 64 same-target gun changes across 17 matches. In known 1014206 it added 48.6 outgoing damage over three seconds with equal incoming and tied placement. Fresh loss 1020304 also added 46.8 early damage at equal incoming and ultimately lost three points.

Joint 1017703 exposed an exact readiness regression. The extra shot reduced ammunition from 10 to 9 out of 12, triggering the next native track reload before engagement resumed. First-three-second outgoing fell from 502.2 to 111.6 at equal incoming. This prompted the [reserve revision](2015a12-preserve-return-fire-reserve.md).

- Survival voted **reject for practice** because independent placement losses and the forced next reload offset the return-shot benefit.
- Combat voted **reject for practice** because the actual reload cost outweighed the first hit in the directed trace and no fresh placement improved.
- Validation voted **revise** to require the native reload threshold still be met after the allowed shot.

The queue received no candidate.
