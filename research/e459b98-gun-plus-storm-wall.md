# Combine the second-step gun and storm wall guard

Candidate `e459b986e1fa6c020da712a1e70fb9bfa3af016f` merges approved `41425de21c0e2e7bf0c48e0881cd1b0bc5926189` and `00192aa51fdef74bb6d7bfd8ad36046c9bef2511`. The changes combine a different movement choice and shot timing. In the full controller, a new shot can suppress the storm override on a shared frame.

Across 108 fresh simulated pairs, four-mech 48 and native campus 12 tied against the verified 3.71 commit. The 24 standard and faster pairs tied against the gun parent, and the 12 standard pairs tied against the storm parent. One joint campus match in 12 fell three points against the storm parent. Both storm fixtures (1027423 and 1037615) and both gun fixtures (1039203 and 1040108) retained every action from the corresponding parent.

Fresh joint seed 1041508 added 55.8 gun damage in the first second at equal incoming damage. Both outgoing and incoming were equal by three and six seconds. Placement fell from 15 points to 12 and the bot lost two kills. The gun-only rerun reproduced all 2,492 combined-build actions and the decline. The unit suite passed 23 tests and the official Docker replay passed with one late response.

Survival voted reject because the combination offered no gain over the gun parent and inherited its loss against the storm parent. Combat and validation voted revise because the exact isolated benefits survived but a cumulative advantage did not emerge. Withheld. Before revisiting, look for an actual match where both changes activate and inspect the effect of new gunfire on the later zone path.
