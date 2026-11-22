# Retain the live line dodge while the rifle is on cooldown

Exact `653e22454fa45107de65e66dc00f5ab406a38e0f` revises immediate parent `f942e3c1689f5f1d73587bf7e239ab47019e0dae`. It keeps the native line-dodge waypoint over an inward closing flank when the sole rifle is unavailable and an observed round from the aligned closing rifle projects through the hull. All three Sol reviewers approved the revised SHA.

In stock simulated 1077270 against the previous queued baseline, only movement changes at 95.8 s. Rival 9's first round still hits at 95.9 s. Its later follow-ups fall from five to three. First-six-second damage is 270→180 incoming at equal 324.95 outgoing and zero storm damage. Life rises 156.05→322.65 s and placement goes from six to nine points. The faster-close and interpolated focal replays fully match baseline commands and placement, so the gain remains specific to the stock replay.

Forty-four fresh pairs tie in placement against `2e2436e4d1ddda95aac8a86c8a18027e276da03c`. These include 20 stock squad seeds, 16 original four-mech pairs and eight independent faster-close squad seeds. Four additional fresh pairs tie against the immediate parent. The finishable hold control ties. All 23 starter-kit tests and 300 timed replies pass. The timed check passed after reclaiming inactive Docker check image storage.

[Prior rule and recorded revise votes](f942e3c-revise-flank-after-recent-rifle-shot.md)
