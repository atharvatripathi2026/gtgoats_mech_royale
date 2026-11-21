# Forecast arrival for post-elimination cube recovery

The exact candidate `f0e1a8dc44d2144aa2337108b9c425fdc7a0e5dd` revises the unqueued `49b22fe2284c4426a575e4e1ad448164ff30422f` movement rule. It uses current momentum, acceleration, current thrust and later walking to select a visible ground-reachable cube within a predicted 2.1 seconds. It keeps the combat command and excludes an actively charged weapon. The finite forecast still assumes the bot can continue toward the cube after the post-elimination override expires within 1.1 seconds.

All 72 fresh simulated campus placements tied the verified `03a8f93` baseline. This includes 24 owner standard pairs from 1025101 and independent 16-pair standard, joint and faster joint sets at 1025701, 1025801 and 1025901. All 48 four-mech placements across six seeds from 1025201 tied. All 24 unit tests and 300 starter sandbox ticks passed at p99 41.6 ms.

In fresh 1025118, the only campus activation, movement alone reached two cubes 0.6 s earlier than verified. The following six-second trades and final win tied. Over the match incoming fell by 520.33 and outgoing by 498.75. An additional exact replay of `49b22fe` on that same public-offer seed found all 3,710 actions and the outcome identical to the revision, so that gain belongs to the earlier rule. The revised candidate also reproduced the prior earlier pickup in 1022118 and preserved every verified action in adverse 1022117. A matched legacy-offer replay of 1025005 activated one tick sooner than the parent, yet restored baseline pickup timing and lost the previous 0.1-second pickup advantage.

## Actual Sol verdicts for the exact commit

- Survival, reject for practice. The rare fresh pickup improvement is real relative to verified, and it already fits the prior range gate. No placement gain demonstrated.
- Combat, reject for practice. Positive charge guard behavior is useful, but the 2.1-second prediction depends on a movement override that can end sooner.
- Validation, revise. The new estimator has no fresh evidence of acting before expiration or of improving the inherited pickup result. Measure native movement and elapsed pickup time after the override ends.

[Parent experiment and votes](49b22fe-movement-only-nearby-cube-recovery.md)
