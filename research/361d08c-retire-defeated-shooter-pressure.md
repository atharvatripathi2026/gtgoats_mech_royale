# Clear stale pressure assigned to a defeated shooter

`361d08c8449b4283459ec6a4b88c7358599e5ee2` descends from verified `03a8f93fb36afa5db4a08f211d1d1aa6dcbcae8e`. It preserves the source of the existing directional damage signal, retires pressure only from a specifically confirmed own player kill, and waits while any projectile or beam is visible. Live sightings, damage, sounds and projectile-dodge decisions continue through the incumbent. The memory affects both route pressure and the non-firing torso scan.

| Fresh simulated panel | Seed start | Pairs | Placement change | Improved / tied / regressed |
|---|---:|---:|---:|---|
| Standard campus | 1022101 | 24 | −10 | 4 / 16 / 4 |
| Independent standard campus | 1023201 | 16 | +10 | 2 / 13 / 1 |
| Joint hull and impact | 1023301 | 16 | −5 | 2 / 13 / 1 |
| Faster joint opponent cadence | 1023401 | 16 | −1 | 4 / 7 / 5 |
| Four-mech | 1022201 | 48 | −2 | 2 / 44 / 2 |

All 23 unit tests and 300 starter observations passed, sandbox p99 26.1 ms. The archive contained 61 windows over 41 of 96 games with lingering native pressure from our confirmed kill. In known 1020314 the first subsequent two cubes came 0.2 and 0.1 s earlier. In joint 1020416 the policy waited until intermittent projectiles cleared, then started the loot route about 0.4 s earlier. Both placements tied.

Fresh 1023208 took its first cube about 1.6 seconds earlier, with identical damage over its first three seconds, and gained nine points. Owner 1022111 lost nine points after a first change of scan direction alone, and had identical damage in its first six seconds. Fast joint 1023410 left evade for loot and subsequently took 67.5 more and dealt 341.6 less in six seconds. The proposed restriction to zero other tracked players would discard the strong standard gain and retain that fast loss.

All three reviewers voted **reject for practice**. The specific stale-pressure transition and earlier pickup occur, but the scope also changes perception and combat exposure. Next screen a movement-only relief that preserves the native torso scan, then require direct earlier collection without worsening the first combat window. The queue received no candidate.
