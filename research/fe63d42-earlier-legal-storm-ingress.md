# Earlier legal re-entry into the storm circle

The approved candidate `fe63d42d2743848f7933309c833577e5b204ba35` is based on verified `03a8f93fb36afa5db4a08f211d1d1aa6dcbcae8e`. It compares the native route with legal ground movements when already outside a high-damage circle. It keeps the predicted earlier route only when it can move while preserving the existing aim, boost, weapon commands and conditions for a dodge or required jet. The forecast includes acceleration and the moving boundary.

| Fresh simulation | Seed starts | Pairs | Placement points |
| --- | --- | ---: | ---: |
| Owner standard campus | 1027401 | 24 | +7 |
| Independent standard, joint, faster joint campus | 1028101, 1028201, 1028301 | 48 | 0 |
| Four-mech generated and campus | 1027501, 1028801 | 80 | 0 |

All 23 unit tests and 300 starter sandbox observations passed. All three Sol reviewers approved the exact commit. [Practice ledger and recorded votes](../queue.json)

- Fresh standard 1027423 changed only movement at 269.7 s. The actual first re-entry accelerated from 5.6 s to 1.0 s, with unchanged first aim and boost. Three-second storm damage fell from 300 to 90 with no damage to an opponent or from one in either run. The candidate won, with 15 placement points versus eight. The new trajectory gave up 283.5 outgoing damage in the first six seconds, then ended with 920 less storm damage and survived 59 seconds longer.
- Fresh joint 1028202 re-entered in 2.7 s versus 3.4 s and lost 160 less health to the storm over the match. It survived 1.25 s longer. Placement and total incoming damage tied, and the candidate dealt 1260 less damage over the match.
- The three directed replays all re-entered sooner. Archived faster-joint 1023412 increased placement points from 10 to 15 and cut the first five seconds of storm damage from 962 to 546. Archived 1025110 re-entered in 0.6 s versus 2.2 s, then exited twice and finished with 490 storm damage versus 220 at the same winning placement.

If testing a descendant, evaluate a heading's margin to both the moving boundary and the next circle. Preserve the verified damage savings at 1027423 and 1023412 and check whether it avoids the re-entry rebound at 1025110.
