# Check the offset rifle ray before taking an airborne shot

Exact `2c56019db176a140a0ec30fa0d63463b396fe859` directly follows `1d135a08dcf92df0f1f1d336bfbaf93885f53259`. When the original target is below the legal pitch and no original weapon can fire, the alternate rifle shot also requires terrain clearance along the projected bore with the actual first-step turret slew. The terrain query uses projectile-step segments. [Initial wall finding](bbb52e8-withhold-centerline-only-airborne-rifle.md)

The revision withheld the original obstructed shot and retained the corresponding clear control. It retained a real fresh-seed 63-damage shot during a boosted dodge and the sustained public-equipment replay gain. The independently replayed 1067728 rifle hits arrived one command later but still added 111.6 damage at equal incoming over three seconds. The six-second trades converged. The late trajectory survived 21.25 seconds longer at tied placement. Other replays also tied placement.

All 64 fresh simulated pairs had identical commands and placement across native and public-equipment 16-mech, phased campus, generated and campus four-mech, and the score-linked baseline. All 23 units and all 300 networkless replies passed. All three roles approved the exact commit.

The terrain forecast uses a nominal projectile ray. Small muzzle changes can block near-edge shots, and a moving rival can intercept a clear shot intended for someone else. In one retained replay this produced a hit on the intervening rival. [Gameplay commit](https://github.com/atharvatripathi2026/gtgoats_mech_royale/commit/2c56019db176a140a0ec30fa0d63463b396fe859)
