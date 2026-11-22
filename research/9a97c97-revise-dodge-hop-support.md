# Require actual ground support before delaying the dodge hop

Exact `9a97c97ae7abaff03aba0c0656b28e72d31e4de1` descends from `2e2436e4d1ddda95aac8a86c8a18027e276da03c`. It delays a native stuck hop during an opening rifle line dodge when the boosted ground continuation appears supported. In directed simulated 1076469, the first change at 5.3 s is jump only. Stock and faster-close both go from one to 15 points and from 90 to 45 first-six incoming at equal 540 outgoing. The saved round arrives later at 6.1 s, after the movement changes. The previous shallow-drop replay 1067975 matches all commands, as do all 44 fresh stock, faster and original four-mech pairs.

A physical replay using unshifted interpolated terrain exposes the support error. At the original favorable pose, the second held step leaves a 0.030925 m floor gap, just over the 0.03 m threshold. A translated Campus control also loses support on step two after the guard suppresses the hop. The coarse Campus evaluator holds a constant sampled floor and misses this drop. All three Sol reviewers voted **revise**. The 23 unit tests and 300 timed sandbox replies passed.

Strict diagnostic `bf5881b65a6682ba1802775850fe8229c28f4b8d` checks unshifted ground at each projected foot. It protects the unsupported step and removes the sole directed placement gain. All four fresh 1077300 pairs match commands and placement. It also passes 23 units and 300 timed replies. Survival and combat voted to withhold it, and validation voted revise pending a supported beneficial activation.

[Previous jump trial](dfe6337-revise-escape-jump-delay.md) · [Related dodge experiment](2026-11-22T1215Z-withhold-post-kill-dodge-carry.md)
