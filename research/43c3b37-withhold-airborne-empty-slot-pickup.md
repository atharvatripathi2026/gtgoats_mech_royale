# Airborne empty-slot pickup

The experiment screened 1,358 archived campus tapes for failed dispatched weapon pickups. Seed 1068856 exposed an empty-slot miss while rising into crossfire. Exact commit `43c3b3780698d8621ad3c9f1b315eb26c3469b88` on `5f0ace9121f41f8ff702c7e94f5494649c4671da` projects the first airborne step and lets the mech coast for one command if boosting would move a native empty-slot pickup outside range. At 0.8 s the only changed command field is boost. Projected vertical separation is 3.998 m coasting and 4.083 m boosting against a 4 m limit.

All outcomes below are simulated. The focal replay on current main `ad3ffbb4e16e501790d5fbe5ca68dbd8497421d3` and weapon-after-fire evaluator `d3c9e5b87c33c5cc14d6f3355cdd931baede62c9` yielded the same result. Coasting equips lightning #8001 at 0.8 s. Over six seconds incoming damage fell from 337.5 to 45 and outgoing damage fell from 225 to 135. Survival rose from 11.55 s to 15.70 s, with both fourth for zero points. In the weapon-before-movement evaluator `dbf3350ed938b82e105f58a5dd5dc00f796a8f4a`, both arms equip #8001 at 0.8 s and take 45 while dealing 135 over six seconds. Survival rises from 14.40 s to 15.70 s and both place fourth. This test leaves server ordering unverified.

| Fresh comparator | Paired matches | Placement and command results |
| --- | ---: | --- |
| Gameplay parent, native campus squad16, seeds 1072940–1072951 | 12 | All placements and full commands tied |
| Gameplay parent, native four-mech, seeds 1072960–1072961 across generated and campus pursuit and crossfire | 8 | All placements and full commands tied |
| Gameplay parent, weapon-after-fire campus squad16, seeds 1072980–1072983 | 4 | All placements and full commands tied |
| Verified scored `03a8f93fb36afa5db4a08f211d1d1aa6dcbcae8e`, native campus squad16, seeds 1072970–1072973 | 4 | All placements tied. Seed 1072972 first differed on aim at 222.9 s |

All 23 unit tests passed and the networkless kit sandbox answered 300 of 300 observations on time, with p99 2.7 ms. Full match and decision traces were retained locally.

Three GPT-6.2 Sol reviewers voted **revise** on this exact SHA. Survival flagged that the late override can cancel boost during an active shell dodge. Combat flagged the 2 mm allowance and dependence on shared movement assumptions. Validation flagged unmodeled laser charge slowdown and extrapolating a first-step test to a whole held command. The candidate was withheld. A successor needs evidence from a wider pickup margin, complete command-interval physics, and quiet coverage where canceling boost cannot interfere with an active dodge.
