# Check forward sight before a moving top-off

`ddf00bcb4478b8079766f09050fa4be93d2ba7db` revises `cba82cca38cc2398a661d1eb1d2f0756f7042848`. It requires two clear rays out of three in the movement direction before topping off a nearly full gun while moving. The rays use 60% of sight range and span half the configured forward field of view. Stationary top-offs and native low-ammunition reloads retain their rules. [Sound-memory parent](cba82cc-reload-with-sound-memory.md)

| Fresh simulated panel | Baseline | Seed start | Pairs | Placement-point change | Improved / tied / regressed |
|---|---|---:|---:|---:|---:|
| Standard campus | cba82cc | 1015401 | 24 | −13 | 0 / 22 / 2 |
| Independent standard campus | cc76284 | 1016101 | 16 | −1 | 0 / 15 / 1 |
| Joint hull and impact | cc76284 | 1016201 | 16 | 0 | 0 / 16 / 0 |
| Four-mech | cc76284 | 1015501 | 48 | 0 | 0 / 48 / 0 |

All 26 units and 300 starter observations passed, with a sandbox p99 of 25 ms. The targeted closed-loop 1015012 replay skipped the reload and fired at 111.4 s instead of 112.7 s, restoring an 89.1 HP hit and one placement point against cba82cc. Stationary seed 1014805 still delayed the first return shot by 0.1 seconds while placing one point higher. On 48 prior sound-memory traces, the gate would block eight high-ammo reloads, three with recontact during the reload. Two stationary quick recontacts remain.

Both owner losses started when the policy withheld top-off after at least one second of continuous travel. In 1015414 recontact took 4.9 s after the suppressed reload request, enough to finish the reload. First-six-second damage was identical and the useful reserve went from 12 to 10 rounds. It eventually lost eight placement points. In 1015422 all first-six-second trades also matched, and the candidate finished five points lower.

- Survival voted **reject for practice** because the owner losses were large and the fresh effective-baseline panels showed no gains.
- Combat voted **reject for practice** because the correction works in 1015012 but the broad veto withholds useful reloads during continuous travel.
- Validation voted **reject for practice** because the far sight rays fail to distinguish all safe moving reloads and leave the distinct stationary risk.

The queue received no candidate for this behavior. Use departure from a genuine stationary hold to test when a new exposure window is most plausible.
