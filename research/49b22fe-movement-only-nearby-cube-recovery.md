# Recover a nearby cube after an elimination

The exact candidate `49b22fe2284c4426a575e4e1ad448164ff30422f` on verified `03a8f93fb36afa5db4a08f211d1d1aa6dcbcae8e` moves toward a currently visible same-level cube within 27 m shortly after eliminating a remembered damage source. It preserves the existing selected threat, aim, and firing commands. It checks the ground route and zone, and requires a grounded bot with no immediate visible threat. A future revision can explicitly guard against release of a charged laser.

Across **88 fresh simulated campus pairs** it gained one placement point with no losses. This includes 24 owner standard pairs from 1023501, 16 each independent standard, joint, and faster joint from 1024401, 1024501, and 1024601, and 16 more faster joint from 1025001. The 48 four-mech pairs starting from six seeds at 1023601 all tied. All 23 unit tests and the 300-tick starter sandbox passed.

The rule activated in two of the 88 campus matches, for five frames total. No fresh activation had an active weapon charge. The only placement gain, 1024607, had unchanged immediate pickup times and six-second damage. In faster joint 1025005 one of four early pickups advanced by 0.1 s and final placement tied. Its first six seconds of damage were unchanged. The candidate took 90 less damage and dealt 2.25 less over the match. In directed 1022118 the bot obtained two cubes 0.5–0.6 s earlier and cut three-second incoming from 41.4 to zero. Both won. The exact candidate preserved every baseline action in three directed adverse fixtures from the prior, broader pressure rule (1022117, 1022111, 1023410).

## Actual Sol verdicts for the exact commit

- Survival, revise. Three earlier regressions were removed and a directed pickup benefit is real. Only two fresh games activated and the lone placement gain had unchanged pickup timing.
- Combat, revise. The five fresh activations produced no repeated pickup benefit of meaningful size. Preserve combat posture and explicitly guard active laser charge in a follow-up.
- Validation, revise. A 27 m destination can exceed the 1.1 s override window. Estimate arrival under current terrain and momentum, and verify both the positive 1022118 and adverse 1022117 cases.

[Directed reachability screen](2026-11-21T053900Z-nearby-cube-screen.md)
