# Fire at a tracked rival that exposes its rear

`078b2b169647977dde1dc7e7be4fdb9850202a9c` builds on verified `03a8f93fb36afa5db4a08f211d1d1aa6dcbcae8e`. It permits a first-tick ready and aligned gun shot on a selected track-only rival with an exposed rear after a recent player damage exchange. It requires enough ammunition to preserve the incumbent's reload decision on that action. The target, leg command and sidearm rules are preserved. A hit can restart the repair delay and a borderline magazine can trigger a native reload on the next observation.

| Fresh simulated panel | Seed start | Pairs | Improvement / tie / regression |
|---|---:|---:|---:|
| Standard campus | 1015801 | 24 | 0 / 24 / 0 |
| Independent standard campus | 1016301 | 16 | 0 / 16 / 0 |
| Joint hull and impact | 1016401 | 16 | 0 / 16 / 0 |
| Four-mech | 1015901 | 48 | 0 / 48 / 0 |

All 23 units and 300 starter observations passed, with sandbox p99 of 33.4 ms. Fixed-input archived replay found 34 same-target gun-only commands across four of 32 matches. In 1014214 two added rear hits gave 189 more outgoing damage in three seconds with equal incoming and one more placement point. In 1014205 one additional rear hit added 67.5 damage and placement tied. Another archived trial missed the added shot and lost one placement point, and a fourth tied. The policy never activated during the 56 fresh traced campus games.

- Survival voted **reject for practice** because the known gain and loss offset and the policy can delay repair.
- Combat voted **reject for practice** because fresh placement tied throughout and the target can turn during shell flight.
- Validation voted **reject for practice** because the verified extra damage appeared only in archived contexts and a miss can spend a round before an immediate native reload.

The queue received no candidate for this behavior.
