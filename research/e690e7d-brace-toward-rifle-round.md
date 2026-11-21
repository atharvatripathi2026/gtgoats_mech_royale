# Brace toward a rifle round · queued

Candidate `e690e7dc4625343b31ce22825aaef76ee11bfb7d` against `742246aaa181b45d34e4e7ee5c6a8740e8130b35`. Turn only the torso during a grounded line dodge if both arms are unavailable and a visible imminent rifle impact can come inside the armor arc. Two directed native replays convert actual 67.5 damage to 45. The projectile-path variant of seed 1067946 independently reproduces that conversion. Both bots finish first under the alternate model. The seven-place gain observed in the original evaluator depends on its downstream trajectory.

In 108 fresh simulated comparisons, 107 placements tied and seed 1068158 improved one place. That active match converted two 67.5 hits to 45 and survived 1.8s less while dealing less total damage. The 20 fresh native and 20 fresh projectile-path validation comparisons used the same seeds in both modes. The exact build passed 23 unit tests and 300 networkless sandbox observations after Docker cache recovery.

Survival, combat and validation approved the exact commit based on the repeated damage reduction and the fresh placement evidence. Queue entry 60 contains their reasons. A remaining question is whether holding an already correct armor angle protects a round that native turning would expose.
