# Transfer only the wall-lead solve onto ranged retention

Exact `5dbbc297ee62df1898a328003f6305866125c96b` uses actual parents `8c569b43ea3dfe6a41c989f7d35a0ebe890193af` and `258d8c63654e9d24dacfa6c4c6a675e4b63b6e5f`. Its sole gameplay change from the first parent is the mortar wall helper and its call. This preserves the retention parent's gun selection and lower-pitch shot logic. [Earlier merge](ecd3e57-merge-ranged-retention-with-wall-lead.md)

Across 68 fresh traced simulated pairs, 16 campus games against the retention parent lost eight points in one loss, and 32 original four-mech placements tied. It gained two points over 12 campus pairs against the wall parent and two over eight versus the verified baseline. The original 1059427 regression restored the stock placement. The directed 1058622 four-mech mortar gain remained one point over the retention parent. Unit tests and 300 timed Docker observations passed.

The first change in new 1059515 was a scope error at 77.5 seconds. The native mortar pitch −0.69884 was legal at the −0.7 minimum, while the proposed −0.71886 clip was illegal. The optional change discarded the usable shot at the same target. Actual first-six-second outgoing rose 13.88 with equal incoming after the decision, so it did not show an immediate damage loss. The trial later lost eight placement points.

All three reviewers voted **revise**. The selective transfer repairs the prior gun change, and the new mortar legality fault is independently observable. Withheld. Keep the native shot when the adjusted mortar pitch falls outside the legal range.
