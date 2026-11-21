# Preserve Servos on a quiet walk with a usable partial magazine

Exact `06caa0379b26eae4128d4603658aaab330e3b57c` from `049c97a20cde4894b94bb39b0f60e37a6406c63d` restores native Servos when a promoted Drum would put the same ammo below the existing quiet reload threshold. It requires a grounded, in-zone walk to loot at least four metres away, no target and no reload in progress. All 23 unit tests and 300 timed Docker replies passed.

In simulated 1062819 the first change was the pick at t234.6. Walking speed rose from 11.7 to 12.64 m/s, and two cubes were picked up 0.2 seconds earlier. The Drum arm finished topping off before the next fight. Servos recovered one place and matched all 3,051 commands of the earlier pure detour. Existing high-gain and reload replays kept their parent commands. All fresh public16, native12, four-mech48 and linked baseline8 placements tied.

The same gate lost two places in archived 1062550 and five in independent joint 1062945. Both targets were remembered cubes absent from the current observation when the upgrade changed, and the standard model tied in 1062945. Survival voted **revise**, combat **reject**, validation **revise**. Withheld. The revision should require the actual selected cube to appear in the current observation.
