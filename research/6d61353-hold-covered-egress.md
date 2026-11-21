# Adjust an egress path that opens a tracked shooter's line

`6d6135352b75f0beb84d1ee05eff31830e8afe6f` descends from `e0e641aeea2223f7a8dc6760188d4e2a939cd8eb`. For a non-firing grounded escape or rotation, it can turn the legs about 25 or 40 degrees to keep sampled hull-height cover over the next four observations. It checks lawful ground and circle margin and leaves weapon and boost outputs unchanged. The sampled rays use current shooter locations. Real movement, the next decision and newly tracked opponents can change those lines.

| Fresh simulated panel | Seed start | Pairs | Placement change | Improved / tied / regressed |
|---|---:|---:|---:|---:|
| Standard campus | 1019601 | 24 | −8 | 1 / 21 / 2 |
| Independent standard campus | 1020501 | 16 | +8 | 2 / 13 / 1 |
| Joint hull and impact | 1020601 | 16 | −9 | 0 / 14 / 2 |
| Four-mech | 1019701 | 48 | 0 | 0 / 48 / 0 |

All 24 unit tests and 300 starter observations passed, with sandbox p99 of 40.9 ms under concurrent load. In fresh 1020516 the new route saved 41.4 incoming damage and added 94.46 outgoing over three seconds. By six seconds incoming matched. The run gained eight points. The two seven-point losses each had equal early damage, one with low pressure and another taking NPC damage in that window. Known 1016002 took the same traced player round despite changing the first steering command. Both routes had returned to a normal dodge before the hit.

- Survival voted **reject for practice** because a predicted course change did not repeatedly avoid the tracked rounds and fresh placement depended on model assumptions.
- Combat voted **reject for practice** because the sampled cover check did not replicate the short-window benefit across the independent models.
- Validation voted **revise** because confirming recent fire from the covered shooter could exclude weak speculative redirects while retaining the one direct favorable fixture.

The queue received no candidate for this behavior.
