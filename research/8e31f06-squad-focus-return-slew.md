# Return to the native gun target

Candidate `8e31f063a24b02988a7f5d1b73fb28b1be33fba1` descends from `a8b8c5b5f4b84501784ade06e4743a12bd6b7ba3`. It permits a brief shooter switch only when the turret can return to the native gun lead before the next shot. It preserves the earlier competing-slot veto and holds the native target for the rest of the current reload when the return would take too long.

Placement and measured endpoints tied across all 136 fresh simulated pairs. Those pairs covered 48 four-mech matches, 72 campus pairs against approved `c1456b5`, and 16 campus pairs against the direct parent on shared seeds. In directed replay 1032803 a 54.5 ms return fit the 190 ms budget, preserving the 59.4-damage opening hit and four placement points. In 1036914 the 272.5 ms return exceeded that budget. The guard restored all 2,433 native actions. The competing-laser replay 1035311 also retained all original actions.

Survival voted approve, citing the preserved first hit and exact repair of the adverse replay. Combat voted revise because fresh placements tied and the native gun feasibility check leaves some secondary fire unexamined. Validation voted revise after finding no target-matched extra player damage in three additional archived activations. All 24 unit tests passed. The Docker rerun answered all 300 observations on time after one late tick in the first run.

Withheld. For a follow-up, look for a fresh, legal shot that actually switches targets and audit secondary fire on frames with no legal native gun solution. A placement tie is expected when the switch never triggers.
