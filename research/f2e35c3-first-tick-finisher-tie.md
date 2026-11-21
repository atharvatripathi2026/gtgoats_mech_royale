# Prefer an aligned gun between similarly ranked finishers

`f2e35c3ac7a6a4faab8a3444f222e45557520de1` descends from burst-finishing parent `6693026eabcde9638c74280595c348382cbbcdb6`. It retains the incumbent engagement and finishing gates. If an already eligible finisher needs at least 0.22 seconds to align, a comparably ranked visible finisher can take priority only when a loaded gun can align for the first physics tick. It preserves an active laser charge and a ready mortar.

| Fresh simulated panel | Seed start | Pairs | Improvement / tie / regression |
|---|---:|---:|---:|
| Standard campus | 1017501 | 24 | 0 / 24 / 0 |
| Independent standard campus | 1017801 | 16 | 0 / 16 / 0 |
| Joint hull and impact | 1017901 | 16 | 0 / 16 / 0 |
| Four-mech | 1017601 | 48 | 0 / 48 / 0 |

All 23 unit tests and 300 starter observations passed, with sandbox p99 of 1.9 ms. Exact fixed replay of 32 archived matches found zero switches. Broadening either eligible participant in exploratory archive screens still produced zero switches. A recent-hit scoring screen changed some rankings but no chosen target and was left unfrozen.

- Survival voted **reject for practice** because every fresh placement tied and the archived switch never occurred.
- Combat voted **reject for practice** because the intersection of two fightable finishers and contrasting turret alignment was too uncommon.
- Validation voted **reject for practice** because both fresh placements and normalized endpoints matched, with no direct archive activation to justify another threshold adjustment.

The queue received no candidate. Revisit only after new data identifies an actual engagement window where the primary target cannot fire and a worthwhile alternate can.
