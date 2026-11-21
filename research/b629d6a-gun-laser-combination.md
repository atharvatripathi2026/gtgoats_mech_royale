# Downward gun plus early laser

Candidate `b629d6a111301439a9e5e35105b6c6575b6af027` combines the approved gun `1d146590e77aad09e012b715e22d20770946287a` and laser `76de1a9ef0db04ddb8e2d43670ba25bc6f300139`. Their firing conditions are disjoint in one decision. The question was whether keeping both options helps over a full match.

Across 140 fresh simulated pairs, all 48 four-mech placements tied. Campus standard and joint sets tied in all 32 pairs against the gun parent. The standard and faster campus sets gained one placement point each against the laser parent over 32 pairs. Against the verified 3.71 commit, the public-offer set gained one point across 16 pairs, and the native campus set lost six points on seed 1040706 across 12 pairs. The gun alone reproduced all of the combined build’s actions in that loss. Comparisons with shared seeds reuse candidate episodes.

The combined policy kept both early beam hits in directed replays. On 1020305 the additional 46.8-damage gun hit preceded the preserved beam, yet placement fell from seven to six and the bot died 55.25 seconds sooner than the laser parent. Unit tests and the official Docker sandbox passed, with all 300 ticks timely.

All three Sol reviewers voted revise. Survival cited the new downside across successive firing windows and the tie against the gun parent. Combat cited the lack of incremental placement benefit over the gun parent. Validation cited the inherited losses and the directed decline despite retaining the laser hit. Keep the parents available separately. For a future combination, compare the six-second sequence after the first new contact against both parents before spending a practice slot.
