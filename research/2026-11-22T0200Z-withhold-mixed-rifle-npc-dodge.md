# Verify a grounded dodge against mixed rifle and NPC rounds · withhold

The scratch extends the existing idle grounded dodge when a rifle and NPC projectile are visible together. The rifle must still intersect the intended path during the held command. Alternate paths check both projectile kinds with their configured radii. An archive screen across 518 tapes found 1,526 distinct qualifying NPC-containing states, 313 actual NPC contacts and two proposed turns.

At 289.4s on 1070733, the exact merge `35662b22040dc59e5aa4a9163505d97e5e62130b` takes a rifle hit on the second physics step. Replaying actual movement and raw terrain confirms rifle 10329 intersects the parent hull and clears the alternate. The alternate changes movement only and extends survival 289.50→290.20s, with equal effective damage, outgoing and placement. NPC 10330 lands on the following command. The other directed case, 1070652 campus crossfire, changes movement but both arms survive 15.05s and the parent takes no hit during the changed command. All eight fresh campus pairs 1071180–87 tie commands and placement.

Survival, combat and validation voted to withhold the unfrozen scratch. A new test needs confirmed current rifle contact and an escape route that remains clear of the visible NPC round after replanning. [Prior rifle route experiment](2026-11-22T0145Z-withhold-downhill-route-rejoin.md)
