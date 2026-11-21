# Start a covered loot pause only while scanning

Exact `21175f88c41caa59b452f26603a932f199a3be5e` is a direct child of `38f245c6d6bc3da212560066cf0d635195c5a769`. It narrows the [earlier cover stop](b67986b-pause-quiet-loot-before-losing-cover.md) to start during native scan. The pause may continue on later frames while the original geometry and loot conditions still hold, including after a target is selected.

The +7 native 1063580 and +9 joint 1063648 persisted. Directed joint 1063645 and four-mech campus 1063603 returned to stock actions. The public loss 1063409 improved from −5 to −3. Its first pause moved from the earlier tracked loss to t220.1, just one scan tick after an engagement. The known rifle-hit isolation at 1063105 and core detour, roof and reload controls still held through their critical windows.

Fresh net across 124 simulated comparisons was +4 placement points. Public24 gained five, stock joint16 gained six across +8/−1/−1, four-mech48 lost two in one match, native12 and linked8 tied, and the faster-house16 lost five in 1063708. In the faster loss, a move-only pause followed two scan ticks after engagement and cut six-second outgoing from 469.8 to 208.8 at zero incoming in both arms. Cleaner stock joint still shows +9 on 1063648, while faster clean joint makes that directed path inactive. The alternate evaluator `882a26120da6c3e5e0c9c6bbb2b4a471bfe1e6f6` shortens house command refresh from 0.5 to 0.3 seconds with the same aim slew and fire timing.

All three reviewers voted **revise**. Withheld. Scan onset addresses previously selected targets but admits a still-risky short break in the fight.

Exact 23 unit tests passed. The final quiet sandbox rerun answered all 300 ticks on time.
