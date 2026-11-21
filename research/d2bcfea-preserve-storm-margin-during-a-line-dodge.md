# Preserve shallow storm margin during a grounded line dodge

Exact `d2bcfeabbe38a6024cd491707782084db9f3703f` descends from merged `049c97a20cde4894b94bb39b0f60e37a6406c63d`. It removes outward motion only for a grounded boosted line dodge near a fixed high-DPS boundary when the short projection introduces no additional observed projectile intersection. Tangent movement, aim, firing and boost are retained.

The native simulated cave at 1060208 retained both same-tick gun hits and avoided its first storm crossing. Storm damage fell from 184 to 40. Six-second incoming rose by 424.58 and total incoming and placement tied, with survival 0.7 seconds shorter. Public cave, the earlier +2 detour and the roof-jet control were action-identical. All 76 fresh first-parent commands and placements matched across public16, native12 and original four-mech48. Eight extra campus comparisons against the linked 3.71 baseline tied on place. All 23 units and 300 timed networkless Docker responses passed.

Survival, combat and validation voted **revise**. The two-step projection explains the initial margin improvement and leaves subsequent firing exposure unresolved. Narrow the experiment to a new triggered case that preserves both the storm and the actual incoming trade before comparing the full policy again.
