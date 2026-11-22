# Combine rifle aim retention and the live line dodge

Exact merge `2d2a7d480f2da4407d5aff0d36307ea7f4e5e68f` has gameplay parents `653e22454fa45107de65e66dc00f5ab406a38e0f` and `9c5f89bd2e77b8049f83a6102ee875998c1f220d`. The guards require different visible opponents and rounds. Aim retention requires the sole visible opponent to be an NPC, while the movement guard needs a visible aimed rifle mech and a live gun round. The policies can still affect later positioning through the match.

In stock simulated 1077443 versus the dodge parent, the first change is aim only at 115.7 s. The same drone's two rifle hits advance 116.2→116.0 and 116.4→116.2 with tied six-second damage and placement. In 1077270 versus the aim parent, the first change is movement only at 95.8 s. The first rival round still hits. Two follow-up hits disappear, taking incoming damage from 270 to 180 at equal 324.95 outgoing and raising placement from six to nine points. Both full gameplay streams match their original policy parent on the respective stock witness.

Independent interpolation reproduces the aim parent's earlier fire command, equal recorded hit time and tied outcome. It reproduces the inactive dodge parent's full gameplay stream on 1077270. The 23 starter-kit unit tests and all 300 timed sandbox replies passed for the exact merge.

[Drone aim review](9c5f89b-retain-drone-dodge-aim.md) · [Live line dodge review](653e224-retain-directed-line-dodge.md)

All 72 fresh parent comparisons match commands and placements. This includes 16 original four-mech comparisons on each parent at 1077700–03, eight stock squad comparisons on each at 1077720–27, eight independent stock comparisons against the dodge parent at 1077640–47, and eight faster-close comparisons on each at 1077680–87. The four-pair +1.75 placement delta versus the verified 3.71 build is already present in the dodge parent, which produces an identical gameplay stream on all four seeds.

The three actual Sol votes and both gameplay parents are recorded together at ledger position 109. [Practice ledger](../queue.json)
