# Increase scan cadence after the first zone hold

All three Sol reviewers voted **reject** on `6015ee731f40ccbc00926afada986f1bfd1dc5cd` against squad focus. The variant preserves the original scan through the first configured zone hold, then speeds up the sweep with continuous phase. It addresses the missed opening pickup in [the always-fast test](e2dedc6-faster-quiet-sweep.md).

On known seed 952803, all 601 opening actions through 60.0 seconds matched. The revision saw pickup 8008 at 4.2 seconds, and its first action divergence was at 60.1. The revised score was 10, compared with three for the always-fast variant and 15 for the baseline.

Across 18 fresh campus pairs the revision lost 0.833 placement points per game (5 improved, 7 tied, 6 worse) and 18.2 seconds of survival on average. All 32 four-mech episode records matched as expected because those episodes end before 60 seconds. The independent campus reserve remains unused. All 23 unit tests and 300 official replay observations passed.
