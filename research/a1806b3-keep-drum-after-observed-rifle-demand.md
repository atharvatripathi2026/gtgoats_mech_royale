# Keep Drum after sustained observed rifle demand

Exact `a1806b3fca7f6d58b18a6eacd2b2d3f7c3f1d6b6` descends from scoped Lens `4bba0d7e864811db371908c99729d0fa8df1248f`. It keeps the original Drum only when the existing rule would restore Lens and the same held rifle has spent at least two current magazines over the preceding 16 seconds. It counts ammo decreases from observations and clears the sample window on phase, equipment or capacity changes. Refills can hide intervening shots and recent NPC work also consumes rounds.

Joint simulation 1062953 counts exactly 24 rounds and first changes only the choice at t136. It restores all 2,755 commands of effective earlier `75945a8` and recovers five places. Five directed controls are wire-identical, including both Lens gains, the previous fade regression, Armor and reload. As a separate check the fractional-cadence models remove the offer split, while the same-state immediate added-ammo model still gains one place. [Model sensitivity](2026-11-21-rifle-cadence-sensitivity.md)

All 160 fresh placements tied, including 24 public, 12 native campus, 48 original four-mech, eight against linked 3.71, 32 validation comparisons in two models, and 36 extra fresh public-offer joint seeds. The archive screen found no other predicted flip across 585 trajectories and 18 joint offers. All 23 unit tests and 300 timed Docker observations passed, with the consumption fixture also passing.

Combat voted **approve for practice** for the direct reload and placement recovery. Survival and validation voted **revise** because the only observed change sits exactly at the retrospectively measured cutoff. Withheld. Test actual recent empty reloads or time spent reloading across newly activated offers before retuning the threshold.
