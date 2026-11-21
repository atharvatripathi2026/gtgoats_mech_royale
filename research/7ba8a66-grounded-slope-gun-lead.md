# Grounded slope correction for gun aim

The exact candidate `7ba8a660a374517896a38f69ebd8950aa8e0f952` adjusts gun lead by the forecast ground height at the location of a steadily moving grounded target. It uses current, intermediate and projected floor samples and allows a shift of 0.6–2.5 m. The base is verified `03a8f93fb36afa5db4a08f211d1d1aa6dcbcae8e`.

Across 72 fresh campus pairs, the owner standard set of 24 from 1025301 lost eight placement points in one match. The independent standard, joint and faster joint sets of 16 each from 1026001, 1026101 and 1026201 all tied. The 48 four-mech pairs from six seeds starting 1025401 also tied. All 23 unit tests and 300 official starter sandbox observations passed at p99 42.1 ms.

Archived 1019411 confirms an added 45-damage shot after the bot raised its pitch by about 0.012 radians. Both versions emitted the trigger and the target and shooter positions were the same at fire and impact. Placement went from 11 to 15 points in that replay. Fresh 1025322 had the reverse mechanical effect. The forecast rose 0.657 m while the target rose only 0.247 m by the hit. Outgoing damage fell from 122.4 to 61.2 in the first second at equal incoming, and the fresh match lost eight placement points. Fresh joint 1026116 also landed an extra 67.5-damage hit at otherwise identical positions. Over the full tied win it finished with 364.1 less outgoing and 345.3 more incoming.

## Actual Sol verdicts for the exact commit

- Survival, reject for practice. The archived hit establishes a possible gain. One sizeable fresh loss and no fresh placement gains leave it too dependent on individual slope movement.
- Combat, reject for practice. Target motion supplies counterexamples in both directions. Keep the verified forecast-overprediction diagnostic for a narrower model.
- Validation, reject for practice. Three-point terrain sampling misses part of future movement. The fresh aggregate and trade risk outweigh the directed advantage.

Next check whether a shorter or capped adjustment based on observed vertical motion preserves the specific causal gains without worsening the fast near-rim miss. [Prior direct-flight diagnostic](654a338-gravity-lead-for-descending-targets.md)
