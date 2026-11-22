# Verify the retreat and pickup range before holding a reversal

Trial `a350d407dbd77e9e1203e6ba18d46d48551c261a` descends from `78418f5942e739a608756b71f44dfcf351fb8a2c`. It holds one preceding grounded evade move when a persistently aimed, closing rival is present and the bot would reverse sharply toward a visible first weapon with an empty rifle still reloading.

In stock 1076203 at t25.7, the move-only change increased next-observation separation by 0.38 m. That difference reversed within half a second. The first-six trades tied at 583.2 outgoing and 45 incoming. The same lightning pickup moved from 56.0 to 50.8 s and eventual placement rose 13→15. The faster-close replay and 1076052 NPC foil both matched all commands. All 16 fresh stock pairs at 1076380 and 1076500 matched commands and placement, and 23 unit tests passed.

Survival and validation voted **revise**. A previous requested command may have missed its deadline, and the hold may give up a pickup that native movement can reach on the next decision. Directly confirm that observed velocity matches the old retreat and simulate both routes for an immediately reachable weapon. Combat gave a preflight approval conditional on further runtime and fresh checks, observing that the present static cover proxy cannot verify whether a rival can fire during the hold.

[Transition diagnostics](2026-11-22T1130Z-loot-pursuit-transition-study.md) · [Queued rifle policy](740aa2f-reserve-rifle-through-npc-dodge.md)
