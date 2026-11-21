# Defer a new laser charge when the target is projected behind cover

Candidate `a60b5e2c924c4ea2dddc4877e717e60061649160` descends from `e87064a570567f6b47d37f4606bd3e843bb68f7e`. During a grounded boost it skips starting an uncharged laser if projected target hull samples become obstructed near release time from two sampled muzzle paths. The screen leaves existing charges, gun fire and movement unchanged.

Of 77 boosted ground charge starts across 132 simulated archive tapes, the screen found two likely closing lines, and neither of those original beams hit. In the exact standard 1040012 rerun, deferring the charge by 0.1 seconds resulted in no displacement gain. In the exact faster 1034502 the mech fell on the first physical step and had the same movement during the immediate exchange. The trial later began a different charge and dealt 63 less over the first six seconds and 538 less overall at tied placement. All 88 fresh placements and measured endpoints tied. All 22 units and all 300 timed Docker observations passed.

All three Sol reviewers voted reject. The proposed sprint advantage did not happen in either directed control even when the veto correctly identified a missed beam. A future test should first show that starting the beam actually caps speed while the mech remains on the ground and that expected movement clearance improves.
