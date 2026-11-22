# Keep rifle dodges aligned with the current route · revise

Exact `41468670c7eb1e6f2a6a442ef489ef9a48a47878` on `f995228262f06e394a5b32ea598c908abd22d990` tests only 15°, 30° or 45° heading changes, preserves native movement magnitude and verifies each grounded axis step. It restores all three earlier focal tapes including the 14-point loss and the generated four-mech loss.

The 16 fresh stock squad pairs (1069580–95) change two tapes, with one tie and one loss. At 39.6s in 1069587 the 30° change genuinely avoids a 45-damage bullet, matches 644 damage dealt through six seconds and survives 11s longer at the same seven points. At 149.3s in 1069589 the same magnitude only delays projectile 10153 by one observation. Six-second incoming ties at 365, outgoing falls from 845 to 690 and the match loses one placement point and one kill. All 16 fresh standard four-mech pairs and five independent phased pairs tie on complete commands and placement. Six more native comparisons tie on placement against the commit-linked reference.

All three reviewers voted **revise** after the fresh placement loss. Exact build passed 23 unit tests and 300 of 300 networkless sandbox observations. A follow-up checks whether the same projectile can still hit on the first physics step after the command expires. [Wide-turn test](a15eb27-revise-rifle-contact-before-replan.md)
