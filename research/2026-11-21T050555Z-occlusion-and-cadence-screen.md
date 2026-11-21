# Occlusion windows and simulated opponent decision cadence

A 64-match archive at verified `03a8f93` contained ten short scan-only gaps where the same gun target reappeared within 0.9 seconds and the gun was ready. In eight, geometry and recorded yaw imply that the previous aim could align on the first physics tick after return. This measures foregone alignment on an unchanged trace. It does not forecast whether the round actually hits or an earlier hit changes later visibility.

A separate 1,293-frame screen of recently engaged targets still in sensor memory while the controller scanned found 44 currently clear hull rays. Only 24 occurred with a ready gun and only two with first-tick aim alignment (1014212 at 188.7 s and 1017701 at 327.9 s). We kept the existing negative visibility cache behavior and focused on the shot-window tests.

We also repeated 16 fresh matched seeds, 1020001–1020016, with the verified controller and the queued projectile-sidestep controller `e0e641a`. Both used the same 16-mech hull and physical impact model. An isolated harness changes simulated house update cadence from 0.5 to 0.2 seconds. This changes the timing and random draws for the simulated opponents.

| House update interval | Verified 03a8f93 mean | e0e641a mean | Change for e0e641a | Improved / tied / regressed |
|---|---:|---:|---:|---:|
| 0.5 s | 7.188 | 7.625 | +7 total | 4 / 11 / 1 |
| 0.2 s | 7.625 | 7.125 | −8 total | 2 / 10 / 4 |

The family ordering flips under the faster simulated opponent. Continue using consistent models within every pair and retain verified `03a8f93` as a baseline when an alternate model favors a descendant. No official attribution follows from this diagnostic. [Earlier cadence check](2026-11-21T023540Z-house-decision-cadence.md)
