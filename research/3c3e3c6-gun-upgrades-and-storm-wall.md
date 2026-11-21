# Combine healthy gun upgrades with the storm wall guard

Candidate `3c3e3c6adc12ff121f33ac8c1e5f87d561e307ec` merges `41425de21c0e2e7bf0c48e0881cd1b0bc5926189` and `8b9f76db264c8aa33e6c70b8ef67c741cb56f60d`. Equipment and storm routing have separate decision branches. Earlier picks can still change which route or fight the bot reaches.

Across 116 fresh simulated comparisons, the combined policy gained 13 placement points in 12 standard campus pairs and two points in 16 joint pairs against storm. All 28 pairs against the gun upgrade parent tied, as did 12 native campus and 48 four-mech pairs against the verified baseline. The five gains and one loss versus storm all had unchanged storm damage. Shared standard seeds contributed to two separate comparator panels.

In replay 1027423, the merge chose a drum instead of servos while rotating. Placement fell from 15 to eight points versus the storm parent. The upgrade-only parent also scored eight points but took 1,235 storm damage, compared with 545 in the merge and 890 in the storm parent. The merge did retain all 4,156 actions in the genuine wall control 1037615 and all actions in the 970605 upgrade gain. All 24 unit tests and all 300 timed Docker observations passed.

Survival, combat and validation each voted revise. The additional placement points inherit the gear policy, and the two features failed to retain the storm win when early gear changed. The servo-only revision tested a more selective pick on the same route. [Servo revision](9daf3cb-retain-rotation-servos.md)
