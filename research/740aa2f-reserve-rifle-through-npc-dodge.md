# Reserve the rifle through an NPC-only dodge

Exact `740aa2ff02444a3f82622298d39baff2621e4e4a` descends from `78418f5942e739a608756b71f44dfcf351fb8a2c`. During a line dodge with NPC-only projectiles, a recent confirmed hit on a visible wounded drone can defer a voluntary rifle top-off. The rifle must have enough ammunition to finish the drone and still have one round. An observed player, mixed projectile, weapon pickup, upgrade or empty rifle blocks the override.

- In directed stock 1076052, the first command difference at 1.1 s removes the reload. Earlier shots add 135 player damage at equal 140 incoming through six seconds, with placement tied at 15. The drone remains alive through eight seconds, while stock kills it at 6.3 s. Stock whole-match kills fall 10→8 while damage received also falls. The same seed under faster pursuit reproduces the 135 first-six gain at equal incoming.
- Independent faster 1076423 first differs at 3.3 s. First-six outgoing 0→121.5, incoming 100→50 and placement 7→10. Survival time falls 252.65→236.55 s. Native 1076470 first differs at 2.9 s and cuts six-second incoming 100→25 at equal zero outgoing. Placement stays at seven and kills stay at six, while survival drops 318.5→180.1 s.
- The 44 fresh parent pairs give one placement gain and 43 ties, with full command ties in 42. The panels used stock 1076400 and 1076460, faster-close 1076420, and original four-mech 1076440. All four reference comparisons at 1076480 reproduce the exact parent commands and placement against the last score-linked official build.
- The exact commit passed 23 unit tests and all 300 timed networkless kit replies, p99 20.6 ms. Initial runtime and traces were retried after recovering disk space. All three Sol reviewers voted **approve for practice** on the exact commit. The tradeoffs in full-game survival remain significant.

[Prior reload trial](2652621-withhold-lethal-second-step-reload.md) · [Queue ledger](../queue.json)
