# Tested cover redirect during a cached evade

Exact `05c0505837799ceeacb147abf23c4d8c75557c4c` uses verified `03a8f93`. It preserves the existing cache, then applies a movement-only redirect when repeated hits identify a dominant visible shooter and a grounded legal alternate is forecast to block the shooter's rays. It leaves current shots, charge, and boost intact.

All 72 fresh campus placements tied, covering the 24 owner seeds from 1031701 and 16 each from 1032501, 1032601 and 1032701. All 48 four-mech placements from 1031801 also tied. All 23 units passed. The 300-observation starter checks passed, with 299 and 297 responses inside the timing budget on the two runs.

The exact fixed replay changed three wire commands in 120 archived games. In the full 1017704 replay, the first change occurred at 216.6 s and native movement resumed after 0.1 s. Both actual hull rays remained exposed at the sampled future times. Over three seconds incoming stayed 37.5 and outgoing fell from 194.4 to 145.8. Final placement points fell from 15 to 4. Limiting the forecast to the two physics ticks actually issued then returning to the native route found zero archive activations.

## Actual Sol votes for the exact commit

- Survival, reject. The intended cover did not materialize in the directed replay, which lost 11 points. No fresh placement improved.
- Combat, reject. No observed hit was removed in the first three seconds, outgoing fell, and timing margin varied in the exact Docker checks.
- Validation, reject. The held heading forecast exceeded the length of the command. Verify the trajectory actually executed before any further continuation test.

[Prior confirmed-shooter screen](cc352c9-confirmed-shooter-cover.md)
