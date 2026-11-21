# Brake a shelter move before re-exposure to a confirmed gun

Exact `e9933d208f79331f1e8481afb213161fffb2a8b5` descends from `02c2fc0726496969bff0f8a735433480fed2797b`. The bot can brake a quiet grounded shelter move after confirmed recent gun damage, when the projected braking path stays covered and the native endpoint opens a ray to that shooter. The 0.4-second estimate holds the current command and the estimated muzzle fixed. [Original covered hold](02c2fc0-keep-a-covered-native-hold.md)

In directed 1054307, the first change at 167.7 seconds affected only movement. The trial avoided 62.1 from the known shooter and outgoing rose from 145.8 to 243 over three seconds. It gained one place and survived 33.65 seconds longer. All 16 direct-campus and eight verified-baseline campus placements tied. Of 32 fresh four-mech pairs, one lost a point and 31 tied. In generated pursuit 1058520, the brake delayed four 46.8 hits by about 0.1 seconds each. An earlier NPC hit raised incoming by 37.5 at six seconds and the trial survived 11.2 seconds less. All comparisons were simulated with full traces. All 23 unit tests and 300 timed Docker observations passed after disk recovery.

- **Survival voted revise.** The directed hit avoidance was real, but the fresh loss showed no net reduction against the player shooter.
- **Combat voted revise.** The shooter reacquired after a short delay and the brake left the bot more exposed to a different source.
- **Validation voted revise.** A one-shooter endpoint forecast misses total exposure even when its ground acceleration model fits.

Withheld. Propagating the observed muzzle across the next 0.4 seconds did not distinguish the two controls. A follow-up should predict whether exposure persists across the actual shelter-to-dodge transition and confirm a changed hit or miss in replay.
