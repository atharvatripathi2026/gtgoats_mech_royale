# Limit repeated-attacker reranking to a ready shot

Exact `d5fbf183c9283d3a52d1ad53dfec1b203a95bb52` descends from `ff1bcd4` and tests against approved `c1456b5`. It uses the last 0.4 s of a measured reload and the first ready shot, with existing sight and estimated turn time. It avoids the prior broad attempt to prefer a recently confirmed shooter while a gun is already loaded.

All 72 fresh campus placements tied against focus (1036301, 1036901, 1037001, 1037101), as did 16 comparisons against the actual parent using the shared 1036901 seeds and all 48 four-mech placements from 1036401. All 24 units passed. The starter sandbox passed with 298 of 300 actions within budget.

Directed 1032803 preserved the +59.4 first gun hit and gained four placement points. It corrected one earlier adverse focus result, but in archived 1035311 a later reload gave up 504 outgoing damage at tied placement. Fresh 1036914 switched from a nearby native target and lost the next gun trigger while turning back. Its full output fell by 713.4 at tied placement. The marked lightning shots occurred at the same moments in both paths.

- Survival, reject. One real earlier hit and zero fresh placement gains, with observed cost of switching in active fights.
- Combat, revise. The first-ready shot is useful, but the existing selected target can warrant a faster shot.
- Validation, revise. Preserve the directed first hit while comparing the turn back and native competing gun action.

[Later competing-fire revision](a8b8c5b-competing-fire-reload-window.md)
