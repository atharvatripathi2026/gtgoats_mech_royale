# Hold an early laser charge through a short occlusion · queued

Exact candidate `10ac8ca8f303348c04aa1c91701774df488892b2` on `b3d67472a42cae1fd989ca452c8296b2770d8ad1`. During a stationary grounded hold, the bot can keep an existing early charge for up to three commands if the previous opponent remains tracked, the target's predicted body clears terrain in both next samples, and no opponent is tracked within 100m. It preserves movement and rifle commands. The gate uses intended movement. Continued holds do not resample the initial sightline test.

In simulated native 1068427 at 160.8s, it held charge and later landed an actual 441-damage beam against the same opponent. Incoming was zero in both for six seconds, and both bots won. An independent projectile-path replay of the same seed and the directed native loot control matched the parent on all actions without activation. All 32 fresh parent comparisons tied on action and placement. Eight comparisons against officially scored `03a8f93fb36afa5db4a08f211d1d1aa6dcbcae8e` gained the same single placement point as the unchanged parent on identical seeds.

The exact build passed 23 unit tests and 300 networkless sandbox observations. Survival, combat and validation approved the exact commit. Queue entry 63 contains their reasons. Repeat an active encounter under alternate opponent motion before generalizing the native hit.
