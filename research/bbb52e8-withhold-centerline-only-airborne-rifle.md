# Airborne rifle needs clearance along its actual ray

Exact `bbb52e80bea0c12f83bc0ce7c7a55c93a068632d` directly follows `1d135a08dcf92df0f1f1d336bfbaf93885f53259`. It switches to an already aligned rifle target on ascent if the selected enemy is clearly below the lower pitch limit and no original weapon can aim. The first version checked clear current and projected lines from the muzzle center.

All 96 fresh simulated placement pairs tied. The four fresh mode changes landed real extra shots. Two windows reconverged by six seconds and two retained extra damage. For example, seed 1067858 dealt 180 extra damage by six seconds and at the end, while incoming, life, kills and placement tied. In 1067728 it dealt 111.6 more damage at equal incoming by three seconds. The six-second totals converged, and the later trajectories diverged at tied placement. One archived replay hit a moving intervening rival instead of the selected target.

Independent validation translated an actual positive observation to another valid point on the same Campus map. The exact policy fired because both centerlines were clear, but the first-step slewed, offset rifle ray encountered a wall. The obstruction persisted across 27 small muzzle perturbations. This controlled observation checks clearance and carries no measured placement loss.

The survival and combat reviewers voted **approve for practice** based on the real hits and clean fresh placements. Validation voted **revise** on the observed wall clearance error. The exact commit was withheld. The next revision checks the projected, offset ray in projectile-step segments. All 23 units and all 300 networkless sandbox replies passed.
