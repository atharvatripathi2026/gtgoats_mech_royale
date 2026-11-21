# Transfer the second-tick gun trigger to the verified baseline

`35114e642507447f5a910b16363ce41336983d27` applies the queued `cc76284` second-tick gun trigger patch directly to `03a8f93fb36afa5db4a08f211d1d1aa6dcbcae8e`. The original gun economy on the verified baseline stays in place. Under the two-physics-tick action protocol the bot holds the gun trigger if cooldown expires and the unchanged primary gun aim aligns by the second tick. First-tick fire and sidearm choice are preserved.

| Fresh simulated panel | Seed start | Pairs | Placement change | Improved / tied / regressed |
|---|---:|---:|---:|---|
| Standard campus | 1021901 | 24 | −10 | 1 / 18 / 5 |
| Independent standard campus | 1022601 | 16 | −2 | 1 / 14 / 1 |
| Joint hull and impact | 1022701 | 16 | −1 | 2 / 11 / 3 |
| Faster 0.2 s joint opponent cadence | 1022801 | 16 | −7 | 2 / 12 / 2 |
| Four-mech | 1022001 | 48 | +1 | 1 / 47 / 0 |

All 23 unit tests and 300 starter observations passed, sandbox p99 25.6 ms under mixed load. In 147,936 fixed inputs across 56 archived matches it added 99 intended gun triggers in 22 matches. One other difference also appeared in the baseline reconstruction. In directed 1015807 the new trigger delivered 72.9 additional outgoing damage at equal incoming and placements tied. In the fresh four-mech 1022004 generated pursuit it increased same-target one-second damage from 48.6 to 97.2 and gained one placement point.

In fast joint 1022801 the new trigger kept the same first-second exchange, then added 394.9 damage over three seconds at equal incoming. The run ultimately lost eight points. In 1022802 the first second also matched and the run lost nine. The cadence panels use independent seeds. Their differences are stress evidence, without a controlled cadence estimate for this policy.

All three reviewers voted **reject for practice** because the verified timing advantage did not yield repeatable placement on this line. Earlier practice approval of `cc76284` concerned another gameplay parent. The queue received no candidate for this behavior.
