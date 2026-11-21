# Preserve the leg-servo offer during a quiet loot walk

Candidate `ed69f00ff57260aacc4e6bda0def2f7798b0f416` descends from `79ae4b2c4a4c6ecba435fb3596dc2c7e240aec61`. It preserves native-preferred servos only when the gun-throughput bonus would instead select the drum, the bot is grounded and in-zone with a loot goal at least four metres away, and no target is currently selected. The gun must have a full magazine and be out of reload. The selected target check does not establish that all nearby space is clear.

In directed 1053410 the only first change was the offer at 123.7 seconds. The candidate's walk speed reached 12.64 versus 11.7. At three seconds it was 1.78 metres from the chosen loot and had collected a cube, while the parent was 3.68 metres away with its original count. Placement rose from five points to 14. The three prior mortar gains, separate gear gain 1053207 and dodge 1044006 kept every action. Of 92 fresh simulated pairs, faster 1056108 gained one point after the same kind of upgrade change and the other 91 tied. The faster route reduced remaining distance by 2.13 metres in its first three seconds at equal six-second trades. It ultimately dealt less damage and finished one place higher. All 24 unit tests and 300 timely Docker observations passed.

All three Sol reviewers approved the exact build. The effects are scoped to the observed offer and travel states.
