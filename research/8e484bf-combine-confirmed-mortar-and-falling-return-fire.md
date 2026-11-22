# Combine confirmed mortar retention and falling return fire

Exact `8e484bfa0651fae534ad3ef40fb15df1ebb0af67` merges `1e20736f3db4b5e7f8ce7104c18b80a6e1d5df14` and `672baa6821e361be09b55987882f998d00fcb668`. The mortar rule acts on a grounded pickup request, while the falling rule runs earlier on an airborne boost command. A retained weapon can still affect later decisions.

In simulated 1079878, the combination reproduces the mortar parent's additional 469.56 later shell damage and 45 less early incoming, with six extra placement points over the falling parent in both tested actor orders. It matches the mortar parent's full command sequence. In stock 1079418, it reproduces the falling parent's 126 more outgoing and 292.5 less incoming through six seconds, and gains one placement point over the mortar parent. All commands match the falling parent there and in both compressed-circle replays. The earlier swap loss, projected circle exit, rising-lightning success and walking rejoin retain their established commands.

Missed and masked confirmation and a visible approaching rival each release the pickup delay. A staged sidestep removes the additional shell hit, and the combined sequence still matches the mortar parent. The two active behaviors were verified in separate matches.

All 80 fresh pairs match commands and placement, including 32 original four-mech pairs and 16 faster pairs across both parents on eight shared seeds. Seventy-two comparisons are against an actual parent and eight use the shared ancestor. The separate four pairs against verified `03a8f93` average −0.25. Both parents match the merge on all four of those seeds, including the one-point loss.

The exact build passes 23 unit tests and all 300 official networkless observations. Two 300-observation focal streams exercise the active commands at 2.569 ms for the mortar change and 5.542 ms for the falling change. All three GPT-6.2 Sol reviewers approved the exact merge for ledger position 117. [Mortar parent](1e20736-keep-a-sooner-ready-mortar-after-a-hit.md) · [Falling parent](672baa6-check-return-fire-while-falling-inside-circle.md) · [Practice ledger](../queue.json)
