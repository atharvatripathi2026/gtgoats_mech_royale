# Withhold the clearance-checked second-step rifle

The local policy changes exact `2d2a7d480f2da4407d5aff0d36307ea7f4e5e68f` in loadout Git blob `b69429a579190a6b3b9664b3e212a023fae4adf3`. It tests supported shooter poses, both launch and target phases, raw and raster clearance, axial spread samples and competing bodies. A final command check revokes the added fire bit if aim or motion changes.

The older 1077191 stock pulse passed through cover only through its sampled spread. The centered ray was blocked. Seed 1077429 failed one pitch ray and 1077430 used the last round against an opponent it could not finish. The strict trial matches parent commands and placements on all three. It fires in three different simulated stock replays. Seed 1077221 advances the same hit by 0.1 s at equal trade, 1077421 records the same hit time and trade, and 1077180 adds 21 outgoing with 180 extra incoming in the next six seconds. All three placements tie. Eight fresh stock pairs at 1077770–77 also match every command and placement. Independent interpolation yielded no active benefit.

Combat voted to withhold this diagnostic before gameplay freeze. The next test should require a real contact with an exposed opponent and a fresh replay where the later native command loses that contact. [Prior timing pulses](2026-11-22T1245Z-withhold-broad-second-step-rifle.md)
