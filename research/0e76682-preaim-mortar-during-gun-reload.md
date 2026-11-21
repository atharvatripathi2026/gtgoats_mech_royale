# Pre-aim a nearly ready mortar during gun reload

Exact `0e7668247d8d3db4d71bf72e065dcea8afc8f576` descends from `02e756efb79ff95d7be6d82e44e98f51fc1bdba6`. It selects the existing mortar aim briefly before the mortar is ready while the gun is reloading and no native eligible shot overrides the choice. Initial movement, target and trigger stay the same. Later visibility and impact direction can still change.

Three directed shells launched and reached the target 0.1 seconds sooner. One match gained two placement points and later took 257.75 extra damage. All 80 owner fresh placements tied. The joint 12-pair panel gained one point and lost one. In 1060641, an earlier shell hit the front instead of the rear, losing 195.76 outgoing by three seconds and taking 90 more by six. In 1060646 an earlier shell gave only a small immediate damage gain. The 12 verified-baseline pairs included an eight-point decline after an aim-only change with unchanged first-six-second trades. The two prior wall controls retained their commands. Unit and timed Docker checks passed.

All three Sol reviewers voted **revise**. Withheld. Pre-aim a repeat shot only after confirmed contact with the same target and retest the target-switch and frontal-hit losses. All comparisons were simulated.
