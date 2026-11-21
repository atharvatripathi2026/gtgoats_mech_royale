# Grounded rifle dodge toward momentum · revise

Simulated 1069100 had a late direction fork at 205.1s, after the last-round aim difference at 133.2s. Copying only the queued controller's southeast move into `3dd4015` changes its result from 8 to 15 placement points and survival from 229.8s to 346.75s. Copying only the older northwest move into `f995228` still wins and reduces damage taken over the next six seconds from 392.83 to 0. Both interventions retain aim, trigger, jump and boost.

The generic test `d2c0bb08792c7136a7f59545527e69f399d2bde5` on `f995228` preferred momentum only if the native path projected a hit and the legal alternate had at least 0.5m spare clearance. The live native hull radius is 2.5m in this evaluator. With ground acceleration and terrain-filtered projectile segments, the focal native and momentum paths both clear the tracked bullets by 1.41m and 5.14m respectively. All commands and placements tied in the directed replay and eight fresh native pairs (1069110–17). It passed 23 unit tests.

The survival reviewer voted **revise** and withheld the scratch commit. The controlled motion changes affected exposure after the immediate projectile pass. A next test should compare legal exits on follow-on sight and cover when both avoid the same shots. [Queued parent review](f995228-confirm-target-through-last-rifle-round.md)
