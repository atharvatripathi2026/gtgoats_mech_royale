# Late-fight descent to regain a shot

The published gameplay commit is `c0727065234f3aa6f87f014e24a3c2c4ed5ac0f3` from the verified `03a8f93fb36afa5db4a08f211d1d1aa6dcbcae8e` baseline. It drops a tactical boost when a visible target is below the gun's reachable pitch. The gate requires clear space below the bot and avoids intervening during a dodge, a required navigation jet, an active shot, or a charged weapon.

| Fresh simulation | Seed start | Pairs | Change in placement points |
| --- | --- | ---: | ---: |
| Owner standard campus | 1023901 | 24 | +2 |
| Independent standard campus | 1024701 | 16 | 0 |
| Independent joint campus | 1024801 | 16 | +1 |
| Independent faster joint campus | 1024901 | 16 | 0 |
| Four-mech, across six seeds | 1024001 | 48 | 0 |

Two placements improved and 118 tied. All 23 unit tests and 300 official starter sandbox ticks passed. The sandbox p99 was 36.7 ms and max 47.5 ms.

- Fresh 1023905 ended with 8 placement points, up from 6. The first changed command at 272.3 s disabled boost. The candidate hit the same rival with lightning at 273.5 and 273.8 s, while the baseline resumed at 274.0 s. It landed its first gun hit 0.1 s earlier. Effective outgoing damage over the next three seconds rose from 306.5 to 351.5 at equal 112.5 incoming.
- Independent joint 1024816 rose from 5 to 6 placement points. The candidate took 45 more damage in the first three seconds. Six-second incoming damage tied at 585 and six-second outgoing rose from 0 to 90.
- In directed standard 1014214, the opening descent cut the next three seconds of incoming from 372.6 to 82.8 and increased effective outgoing from 0 to 77 at tied placement. In directed joint 1017702 it increased incoming from 1308.6 to 1405.8 with no outgoing and tied placement. Lower altitude can still leave the bot outside usable horizontal range while exposing it to incoming fire.

Reviewers each approved the exact commit for a practice run. [Queue and recorded votes](../queue.json)
