# Pin the raw-rifle activation time

On simulated stock `1074588` with exact `ec95bb3`, the expected single-cube boost advances collection from 171.3s to 171.2s. In the full-session raw replay on evaluator `48cbbb1`, all commands match the parent and the pickup does not activate. Repeating the raw model with `GTG_RAW_RIFLE_AFTER=171.2` restores the observed first motion change, 15→16 cubes one command earlier, zero early trades, the same winning placement and 1.25s less life.

Earlier reports used matching source and evaluator hashes with different values for this runtime control. The parent input divergence at 25.1s was an NPC HP change from altered rifle contact. Record the activation time with future comparisons. [Exact quiet-sprint review](ec95bb3-one-cube-without-upgrade.md)
