# Withhold pursuit carry across the loot transition

The initial hypothesis was to keep pressure from a committed pursuer when the bot enters loot mode. In stock 1076052, the actual hit and kill of #4 preceded the loot switch at t33.6. The next rear rifle hit came from #2. Under faster pursuit, #4 died at t35.2, native evasion continued against #15, and looting started at t37.0 after #15 separated. Validation found no live pursuit by #4 at either loot transition. Its independent early-damage trace also showed that an NPC-only burst can coexist with an unrelated visible player.

Survival voted to withhold the forced carry after controlled stock replays. Carrying loot heading into active evasion lost placement 15→6. Carrying the preceding evade heading into t8.4 loot for 0.1, 0.2 or 0.3 s lost 15→11, 9 or 8. The 0.4 s pulse kept placement tied and extended survival, making the result sensitive to duration. These were diagnostic interventions before a gameplay commit was frozen.

A separate stock 1076203 frame shows an almost 160° reversal into loot while the rifle is empty and reloading and a closing aimed rival has a clear ray. A one-command held-heading diagnostic gained two placement points at equal first-six trades. The next test needs a repeatable observable gate for the reversal, a control where the weapon is ready, and independent faster pursuit.

[Previous handoff](2026-11-22T112844Z-cycle-handoff.md)
