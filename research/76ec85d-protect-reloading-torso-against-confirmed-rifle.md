# Protect the torso against a confirmed rear rifle during recovery

Exact `76ec85d5a0f171b1164a7545baa5f4b3cecdb59f` descends from `a82473cbe4926108660ccd677a51424084dda265`. It uses a recent actual rear hit, the same visible aiming gun rival and a window when no equipped weapon can fire. It turns toward the nearest frontal aim without newly exposing the rear to another visible aimed rival. Ready-laser and opposing-gun controls preserve the original aim.

In directed simulated 1077530 and 1077270, same-source rounds convert from 67.5 rear to 45 front damage and retain the next rifle shot timing. Another 1078432 replay converts two such shots before an additional later hit while surviving 0.25 seconds longer. All four directed placements and six-second totals tie. An all-move-first evaluator repeats the 1077530 conversion, with the recorded projectile path itself also placing the shot inside the new front arc. The interpolated focal 1077270 fully ties.

All 44 fresh simulation placements tie. Of these, 43 match every command and one fresh four-mech pursuit changes aim without changing early trade or placement. Exact 23 starter-kit tests and 300 timed replies pass. All three Sol reviewers approved exact ledger position 112. The general guard estimates attack bearing from the shooter and cannot independently guarantee the direction of every already-fired round or return aim time.

[Practice ledger](../queue.json)
