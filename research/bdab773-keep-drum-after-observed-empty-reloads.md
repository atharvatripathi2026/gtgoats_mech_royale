# Keep Drum after two observed empty reloads

Exact `bdab773ad52f2e5ba1ca66245b1e1d9d4961934e` is a direct child of scoped Lens `4bba0d7e864811db371908c99729d0fa8df1248f`. It keeps sustained Drum only when the parent would restore Lens and the held rifle has actually begun two empty reloads within three nominal firing and reload cycles. Same-phase, same-slot and current magazine checks limit which observations can supply evidence. Partial top-offs provide no evidence.

Joint 1062953 saw starts at 124.9 and 131.1 seconds before the t136 offer and recovered five places. Prior Lens gains 1062310 and 1011217, fade regression 1011103, Armor and reload controls kept their commands. Fresh joint 1063447 supplied two starts after an existing Drum; the rule correctly preserved native Lens and all 2,886 parent commands. The archived screen found no additional predicted change in 862 trajectories and 23 joint offers.

On the same directed 1062953 input, thinning slot observations to one in 16 rows retained Drum across all 16 offsets. The earlier raw-round gate retained it at three offsets. This is an observation robustness check on one known input. All 160 fresh placements tied, including 16 with independently randomized upgrade draws under evaluator `b16d6b3f81af21cc2b6d33a1e986094b7832a497`. 23 units, a reload-transition fixture, and all 300 sandbox replies passed.

Combat voted **approve for practice**. Survival and validation voted **revise** because the placement gain still comes from one activating replay. Withheld. Recent player pressure may help distinguish a true rival-facing reload bottleneck from NPC or crate work. Test that distinction on separate active offers before changing the window. [Earlier rifle-demand review](a1806b3-keep-drum-after-observed-rifle-demand.md)
