# Restrict post-cap cube detours to a nearby upgrade threshold

Tested `ae029c5dc6ff4618f464c318a3777e5adead8d6b` against `367287e08745649c728a9cbee2ad2311ac781156`. After the HP and damage cap of ten, the change pursues a cube only if enough visible ground cubes are nearby to reach the next upgrade. Incidental pickups and the preceding loot logic remain available. In 64 prior exact logs, the baseline chased post-cap cubes for 2,439 ticks across 19 games and reached the first extra upgrade threshold in four.

| Simulated sample | Pairs | Placement points per game | Improved / tied / worse |
| --- | ---: | ---: | ---: |
| Public upgrades with fixed hull, 972001–972024 | 24 | +0.125 | 2 / 22 / 0 |
| Public upgrades with scaled hull, 972101–972116 | 16 | −0.125 | 2 / 13 / 1 |
| Legacy four-mech, 972201–972206 on both maps | 48 | 0.000 | 0 / 48 / 0 |

In scaled seed 972112 at 77.6 seconds, the incumbent pursued one of two visible cubes 31 m away after reaching ten. The trial continued its zone route. The trial dealt 63 less in the first second and eventually placed four lower. The incumbent reached 15 cubes at 138.6 seconds and finished with 19, while the candidate finished at ten. The change overlooks the ability to build up to one upgrade across several partial pickups. Conversely, a fixed cluster test where cubes span opposite sides can start a short detour and leave the bot only one cube closer when the remaining cubes drop out of range. All 25 tests and 300 starter-check observations passed.

Survival and validation voted **revise** because the nearby count misses feasible progression and does not guarantee that a complete cluster is reachable. Combat voted **reject** because the gain reversed under scaled geometry and was practically flat overall. If revisited, consider only the extra travel needed for partial pickups, preserving cube pursuit aligned with the regular route.
