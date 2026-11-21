# Revise the gun-finisher lightning veto

Exact `acc96a41699afd27aec62d9692ec867b011c1612` compares with `a8543c76bb20d8efb712f1fffd05e0fc95b41690`. It saves an optional fringe arc only after an ammunition decrement, a recent same-target gun hit, and a projected shot that can reach a conservative portion of the target hull within one command. The protocol omits our projectile positions and the prediction uses estimated aim, motion and damage.

In simulated 1061403 the gun shot fired at 220.0 s. Suppressing the 220.1 s lightning still let the actual 86.4-damage rear gun round finish the 72.45-HP target in the same interval. Placement tied on main and gained two with the public-upgrade evaluator, with 270.08 more late incoming in that variant. The 1061414 follow-up and the useful lightning kill in 1061542 matched the parent’s actions. All 104 fresh placements tied across 16 owner public-upgrade campus seeds 1061560–75, 16 independent main campus seeds 1061680–95, 64 original four-mech games 1061700–07, and eight linked official-anchor seeds 1061710–17. Exact 22 unit tests and 300/300 timed official Docker responses passed.

- Survival voted revise. The same-interval gun kill is real, but the energy saving has yet to recur prospectively, and the directed later trade was mixed.
- Combat voted revise. Confirming ammunition leaves uncertainty about the shot path, spread and the target's front or rear damage.
- Validation voted revise. Test a gun ray whose conservative margin survives consecutive observed velocity estimates and the documented spread, and retain a turning control where the lightning shot genuinely saves a miss.

The exact commit was withheld. [Lightning reserve parent](a8543c7-relax-lightning-reserve-when-separation-grows.md) · [Starter kit and protocol](https://www.joinbuilders.org/buildathon/tracks/builders)
