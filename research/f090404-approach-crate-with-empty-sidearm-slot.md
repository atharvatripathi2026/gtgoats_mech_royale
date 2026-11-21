# Approach the engaged crate while the sidearm slot is empty

Exact `f0904041aa541a940db2e544536a33877ede8557` revises direct parent `03a95ca2a82bb55579b6c41609b79a319b4d7169`. The extra inventory gate only allows the crate approach while fewer than two weapon slots are filled. The approved equipment comparator is `74d0c1f895006b573a9fd745a2dba9ae75b57be2`. [Broader variant](03a95ca-approach-the-first-engaged-crate.md)

The revision restores all 235 stock commands in 1059821, including the first cube and placement that the broader policy lost. It reproduces all 3,243 commands in successful directed 1058003, including 0.1-second earlier cube and exact laser pickup and a later three-point gain. It also gives up the old 1060101 gain after the sidearm is already filled. These are simulated results.

All 48 fresh placements against `74d0c1f` tied. Of these, 47 command traces matched exactly. In 1060121 it again obtained the same cube and laser 0.1 seconds earlier at equal six-second player trades. It tied placement with 949.50 more total outgoing, 424.80 less incoming, and 11.15 seconds less survival. Twelve fresh comparisons against the actual broader parent tied. The eight against official-linked `03a8f93` lost three net points, with the changed placements beginning at inherited opening boosts. Fully traced results isolate the earlier acquisition from the full trajectory differences.

All three roles **approved for practice** on gameplay evidence. All 22 units and all 300 local starter-kit observations passed on time. The official Docker image built, but the daemon exhausted disk before ready on both runtime attempts. Queue publication is pending exact Docker verification. The exact commit and its lineage are preserved in the local `research/0945-empty-sidearm` branch.
