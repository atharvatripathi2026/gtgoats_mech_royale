# Replace an unused lightning arm with a mortar at range

Queued `08f3a69150895622e401fc90c1fe60d45a26d0e8` descends from the broad test `a55e7b823807c9276b32fa66eddb7e831b6c1ee7`. When the gun and lightning are held, lightning has no recent player hit, observed opponents are outside its range buffer and the native engagement and zone leave room, the policy can prefer a nearby usable mortar. It preserves the primary gun and existing movement. The muzzle and aim checks approximate shell viability.

Across 88 fresh simulated pairs against approved `e87064a`, joint campus 1051603 gained six placement points after the first mortar hit dealt 312 and killed the selected rival. It gained 918.28 outgoing damage by six seconds at equal incoming. Generated four-mech crossfire 1051402 gained one point and added 338.47 outgoing through three seconds at equal incoming. The other 86 placements tied. Directed 1040002 retained the original four-point mortar gain. The previous adverse laser case 1044805 reproduced the approved parent commands. All 22 units and 300 timed Docker observations passed, with p99 33.0 ms.

All three Sol reviewers approved the same commit based on real mortar hits in independent fresh matches and retained lightning on the adverse replay. The gains are simulated and come from two matches. [Broader trial](a55e7b8-long-range-sidearm-replacement.md)
