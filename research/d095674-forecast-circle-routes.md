# Forecast circle preferences in obstructed routes

Tested `d0956745664aca45347a2c27e1192219561edf30` against `489c7211da0f707e27bba0741abf487fe084871e`. The trial soft-weighted the existing A* search toward the three-second forecast circle while grounded near its edge with an inside goal. A legal exterior route remained available.

| Simulated sample | Paired games | Placement points per game | Improved / tied / worse |
| --- | ---: | ---: | ---: |
| Campus squad, 961001–961024 | 24 | +0.042 | 2 / 20 / 2 |
| Independent campus squad, 962401–962416 | 16 | −0.563 | 0 / 14 / 2 |
| Four-mech, 961101–961106 across two maps and four scenarios | 48 | 0.000 | 0 / 48 / 0 |

In four motivating replays, zone damage changed by −128, −3, −514 and +488 HP. Three placements tied and one was lower. Independent seed 962408 had equal damage dealt and received through six seconds after steering diverged. It eventually fell from first to eighth without zone damage in either version. The tested route cost changed the encounter geometry despite addressing an apparent circle-escape error.

All 23 unit tests and 300 starter-check observations passed. The starter stream stays in the opening circle. In a separate sample of 421 late obstructed decisions the candidate p99 was 19.81 ms and its maximum was 27.95 ms on this host.

| Sol reviewer | Practice vote | Reason |
| --- | --- | --- |
| Survival | Reject | Pooled squad placement fell 0.20; route changes and extra compute produced no repeatable improvement in the known cases. |
| Combat | Reject | The two fresh independent changes lost placement. Reduced zone exposure in retrospective cases did not carry to fresh outcomes. |
| Validation | Revise | The soft cost can change the route on dodge eligibility transitions and failed to preserve the motivating savings across fresh games. |

Retire this exact route change. Future positioning work should pair each proposed movement with the actual incumbent command and measure whether incoming damage changes immediately, before drawing conclusions from the final placement.
