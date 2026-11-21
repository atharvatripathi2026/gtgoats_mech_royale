# Second-tick trigger under impact-direction bearings

Compared queued `cc7628485b7b5ea5b53f51af18baec5e624bd86a` with exact parent `8b9f76db264c8aa33e6c70b8ef67c741cb56f60d`, using the public upgrade arena with [directional impact bearings](2026-11-21T030538Z-impact-bearing-calibration.md).

| Simulated sample | Pairs | Placement points per game | Improved / tied / worse |
| --- | ---: | ---: | ---: |
| Previously matched seeds with old bearings, 982501–982516 | 16 | +0.375 | 1 / 15 / 0 |
| Same seeds with corrected bearings | 16 | −0.125 | 0 / 15 / 1 |
| Fresh seeds with corrected bearings, 990601–990624 | 24 | +0.500 | 3 / 20 / 1 |

In fresh 990604, the additional first-second outgoing damage was 75.6 with no increase in incoming damage. Further corrected replays had immediate gains of 45, 45, 54 and 63 HP while placements tied. The nine-place gain in 990614 had equal first-second damage, so that large placement change cannot be attributed directly to the first extra shot. The public protocol supports holding the gun trigger for the second physics tick. Model and seed sensitivity still matter for final placement.

An archive scan of 56 games found 43 existing both-weapon decisions where laser aim was selected and the gun would first fire on the second tick. In all 43, the commanded torso aim already settled by the first tick. There was no observed benefit to suppressing apparently misaligned secondary-aim gun triggers in this sample.
