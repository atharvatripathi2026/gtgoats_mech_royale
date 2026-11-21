# Prefer cover between clear rifle dodges · revise

Exact `4a94cb563aa44625bffa69ac0bc939c781d4b318` on `f995228262f06e394a5b32ea598c908abd22d990` compares reliable ground paths on both sides of a rifle dodge. It changes only the emitted movement direction when both constant-command paths clear current bullets and the modeled opposite path gains full cover from the one aimed rival.

In simulated 1068991, the only confirmed natural activation, the mirror emits at 238.6s and native steering resumes at 238.7s. All three actual body-height rays from rival 13 stay open in both arms through the predicted cover window. A rifle projectile present at the mirror disappears only in the candidate when it takes an extra 45 damage. First-six incoming ties at 270 and outgoing rises from 1173.74 to 1851.12. Both win with 12 kills and 328.2s survival. The forecast cover never occurs.

Both previous focal controls (1069100 and 1068517) and all 48 fresh parent matches tie on commands and placement (28 native, 16 standard four-mech, four independent phased). Six additional games against the commit-linked 3.71 reference tie in kills and placement. Exact build passed 23 unit tests and 300 of 300 timed networkless observations.

All three reviewers voted **revise**. Survival and validation verified that the brief mirrored command never reaches the projected cover. Combat traced the extra hit to a likely already-observed round. A separate boost-only intervention in 1069100 saves 1.7 energy but adds early incoming damage. Test alternatives based on the actual command interval and verify the next native decision can maintain a safe route. [Prior dodge intervention](d2c0bb0-revise-grounded-rifle-dodge.md)
