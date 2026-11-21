# Angle opening travel after repeated NPC hits

Exact `5e1a727d153079e4837a996171241d07cb2eaa2f` descends from `74d0c1f895006b573a9fd745a2dba9ae75b57be2`. It angles low-urgency grounded travel when the native move heads toward a visible NPC that recently hit twice. It checks a walkable path and leaves the immediate aim and trigger command intact. The initial side preference comes from the slot, so the route can diverge without measuring the next shot line.

Directed 1060135 avoided an actual 37.5 damage at equal early outgoing. The bot still won but later took 483.5 more damage, dealt 1,495.54 less and survived 16.45 seconds less. All 92 fresh same-parent actions and placements matched across the original and joint evaluators. Twelve fresh verified-baseline pairs gained 19 total points through inherited opening behavior. Unit and 300-tick networkless Docker checks passed. These are simulated outcomes.

Survival and combat voted **reject**. Validation voted **revise**. The immediate local avoidance is real, and the changed longer route had a different trade. Withheld. Require a predicted incoming path that distinguishes the safer side before turning away from the native route.
