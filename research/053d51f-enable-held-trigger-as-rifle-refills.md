# Enable one already-aimed trigger at the end of a rifle refill

Exact `053d51fe4ca47e6bbe531496fc080d207eb34fff` is a direct child of `38f245c6d6bc3da212560066cf0d635195c5a769`. It adds a gun trigger only in an existing grounded line dodge, after an observed near-complete empty reload, when the same commanded aim projects a clear second-tick hit on the selected mech. It preserves the other weapon, aim, movement and upgrade decisions.

Directed 1063340 lands an actual 46.8 gun hit 0.1 seconds sooner and gains two places. Six-second incoming is identical, and final incoming is 1,349 higher through longer survival. Both queued reload positives and the quiet reload kept all commands. Alternate evaluator `d155235c3fe3d466d5323f68adc3aacc9a8d3a06` allows the trigger on the refill tick. The same seed ties all 1,421 commands because its changed prior trajectory removes the line dodge at the triggering observation. This identifies seed-level sensitivity to refill ordering and the resulting movement as a combined change.

Two other exact archive activations lost three places in public 1063048 and two in native 1063361. Both added real early outgoing at equal incoming and still lost. The 84 fresh placements tied. Two public activations advanced hits by 0.1 seconds with identical damage totals and placement. 23 unit tests and all 300 timed responses passed.

Survival and validation voted **revise**, combat **reject**. Withheld. Use a real pressure and target continuity discriminator before another timing rule. The public loss occurred with boost active, so a boosted-only gate would keep it. [Queued reload review](38f245c-delay-post-drum-top-off-before-target-acquisition.md)
