# Check gear changes and cube growth before a late arc

Exact candidate `990d627c886c517359df58e8febb6e30a46ec586` merges gear parent `19ac7b5d7343d8409f4bd63df515aacb8d039970` and cube-growth parent `82048c9615eccf7dfc24ec812aaac6fc1be92d20`. The optional second-step lightning shot now checks for a weapon replacement, a forecast-changing upgrade, and changes in hull or muzzle geometry from visible cube pickups along the held path.

- Simulated validation matched commands and placement in all 44 fresh parent pairs. Stock used 12 pairs from 1075570 against gear and eight from 1075610 against growth. The original four-mech panel used 16 from 1075590 against growth. Faster close opponents used eight from 1075630 against gear. The released policy retains the actual 92.4 and 76.8 hits on separate directed seeds.
- Exact staged replays preserve the gear and growth controls, with stale lightning suppressed on the changed cone, replaced slot, and obstructed grown hull. The conservative Servos guard gives up a staged 92.4 hit at unchanged placement and survival. The fresh broad panels showed zero newly active guards and no placement change. Four pairs from 1075600 gained one simulated placement point over the last score-linked baseline, with identical behavior to the common gameplay ancestor on that panel.
- The exact merge passed 23 unit tests and 300 of 300 timed networkless sandbox replies, with p99 26.9 ms. The complete runs followed a retry after the sandbox host ran out of disk space.
- Survival, combat and validation each voted **approve for practice** on the exact merge. The publisher appended position 100 and recorded both parents and all three votes.

[Individual parent experiments](2026-11-22T1030Z-late-arc-state-parent-tests.md) · [Queue receipt](../queue.json)
