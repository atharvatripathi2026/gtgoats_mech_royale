# Withhold the aimed-cover and early-crate merge

Exact `15cabf00d18f3678e03794edf9fb8074c9ab8478` merges aimed-cover `af1b2ab38184da943b05aa4072a8f6b90fc2d03c` and early crate `f0904041aa541a940db2e544536a33877ede8557`. The cover code checks a hold and the crate move follows native selection during farm mode. Earlier gear and movement can alter whether a later covered hold occurs. The exact merge retains the crate parent’s first equipment behavior.

All 100 fresh simulated comparisons against `f090404` match on commands and endpoints, across standard 1062100–19, original four-mech 1062120–27, and public-upgrade 1062180–95. All eight directed controls also match the crate parent. The old aligned cover cases 1054303 and 1061465 have different encounter histories on this family and show no added cover action. A 122-episode archive screen found zero qualifying aimed-cover frames on the combined trajectory. Against `af1b2ab`, the merge lost 18 total in 20 campus pairs and gained two total in 64 four-mech pairs. Its 16-point gain in eight official-linked comparisons was identical to `f090404` action for action. These changes are inherited equipment-family effects.

- Survival voted revise. Independent parents do not establish a combined advantage when all observed comparisons match the crate branch.
- Combat voted reject. The cover interaction never occurred, and the campus loss versus the cover parent matters when choosing the early-equipment ancestry.
- Validation voted revise. The observed gains are inherited and distinct source paths have not exercised a new interaction.

The exact build passed 22 units and delivered 300/300 on the quiet Docker rerun. It was withheld pending direct evidence of a new covered encounter on the early-crate family. [Cover parent](af1b2ab-keep-aimed-cover-on-the-scored-baseline.md) · [Crate parent](f090404-docker-recovery-and-independent-retest.md)
