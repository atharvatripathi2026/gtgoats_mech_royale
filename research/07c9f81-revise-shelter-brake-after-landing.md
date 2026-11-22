# Revise the shelter brake after landing and during rotation

Trial `07c9f8191e1d931055fa13d49e4f4e8c714685b7` descends from `231f8bbfda413fa4b4f0f2ea85981ee41e94eda1`. In stock 1076051, six lateral-only shelter commands left the raw cover in place. First-six incoming fell 180→90 and outgoing fell 413.1→90 against the same rival. Placement rose 8→15 and survival rose 235.7→273.5 s.

The same seed under faster pursuit first braked on the first grounded observation after two airborne frames. Early incoming improved 382.5→180 and outgoing 822.9→990, then placement fell 10→1 and lifetime 257.25→70.85 s. A different rival caused the later damage. Root fresh stock 1076210 also triggered during zone contraction and lost one placement point despite improving the opening trade of that engagement. Across 48 fresh parent simulations there were 47 full command and placement ties and one loss. Four historical-reference placements tied.

Survival, combat and validation each voted **revise** on the exact trial. It passed 23 unit tests and all 300 timed sandbox replies after Docker disk space recovery. The next policy checks for consecutive grounded observations and confines this shelter brake to the opening hold before the first contraction.

[Previous cycle](2026-11-22T110608Z-cycle-handoff.md)
