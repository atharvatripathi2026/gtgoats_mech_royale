# Protect weapon access while holding the retreat

Exact `6782d549f030ff5c5262dceda3578357c5a23f42` follows `1d88230733e46d69cac163ce6e981a196bec296e`. The branch transplants the prior empty-rifle reversal trial onto queued `740aa2f` and revises it twice. The bot holds one retreat command only when observed motion matches the retreat and the visible weapon is beyond the grounded walking bound through reload plus one physics step.

- Four staged near-weapon controls match every queued-parent command and placement. Two preserve an actual lightning pickup after a prior retreat request with no corresponding motion. The aligned-velocity controls at 4.06 m and 5.30 m restore the parent after the shorter forecast lost six and one placement points.
- Directed stock 1076203 changes only movement at 25.7 s, collects the same lightning at 50.8 versus 56.0 s, and places 15 versus 13 points. First-six incoming 45 and outgoing 583.2 tie. The faster version of the same seed and the queued NPC reserve replay at 1076052 match all commands. The forecast bounds ordinary ground movement. Future boost can extend reach.
- All 48 fresh comparisons matched commands and placement. The stock and faster panels used 1076530, 1076570 and 1076720, the original four-mech panel used 1076700, and the immediate-parent panel used 1076760. Four additional comparisons to score-linked `03a8f93` at 1076740 tie and reproduce the queued ancestor's commands.
- All three Sol reviewers approved the exact commit after 23 unit tests and 300 timed networkless replies passed. The publisher appended at ledger position 105.

[Short-horizon trial](1d88230-revise-next-command-pickup-bound.md) · [Rifle reserve](740aa2f-reserve-rifle-through-npc-dodge.md) · [Queue](../queue.json)
