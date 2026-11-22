# Revise the longer quiet post-kill rifle scan

Exact `517b871b98470ccbdd95c02c67fc34b095777b0c` on `b764213e3c589dda158b05f09a3a8dd4ad8687d6`. After a quiet rifle-only kill, continue the native initial turn direction until an observed field of view has passed. The last command can carry the turn beyond that angle.

In simulated 1073494, the already-clear rival appears at 35.8s instead of 36.4s. The first rifle hit lands at 36.5s instead of 37.2s. Six-second damage gains 145.8 at zero incoming and stock placement gains four. Raw firing also gains four. The faster model keeps the early gain and loses one place. Of 36 fresh parent matches, 35 tie commands and placement. On stock 1074561, earlier contact adds 291.6 outgoing at zero incoming, but the earlier kill changes the subsequent loot target. The bot ends with five cubes instead of seven and loses three points. The four separately tested reference matches gain two total points. All 23 units and 300 timed networkless replies pass.

Survival, combat and validation voted **revise**. Test whether the loss persists after limiting the sweep to one observed clear sector or controlling the next loot-target choice after the earlier kill. [Earlier quiet scan trial](e2dedc6-faster-quiet-sweep.md)
