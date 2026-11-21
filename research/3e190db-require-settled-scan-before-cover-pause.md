# Require one rifle cooldown of scan before pausing

Exact `3e190db319ef89d9d5b07d72809eeae03ced7b8f`, direct child of `38f245c6d6bc3da212560066cf0d635195c5a769`, adds one nominal configured rifle cooldown of continuous scan before starting the [scan-only cover pause](21175f8-start-a-cover-pause-only-while-scanning.md). Once started, the same dynamic range and cover checks govern continuation.

The +7 native and +9 joint controls persisted. Both public 1063409 and faster-house 1063708 lost four places after the first pause moved later. The first latter change moved from t58.9 to t59.3 and then sacrificed 313.2 outgoing through six seconds while saving 45 incoming. Both larger losses followed a real line dodge within 0.8 seconds. The three preserved positive contexts inspected had at least 2.5 seconds since a line dodge. A recent-dodge guard is a distinct next experiment.

The 120 fresh simulated comparisons gained 11 places overall. Public20 gained eight net, native12 gained three, four-mech48 lost one, linked8 and canonical joint16 tied, and faster-house16 gained one net. Both faster activating traces improved six-second outgoing, with eventual placements +2 and −1. Exact 23 unit tests and all 300 timed responses passed on the rerun.

Survival, combat and validation voted **revise**. Withheld. Waiting longer for scan preserves favorable openings and still pauses during the recontact window.
