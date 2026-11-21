# Nearby wall veto for storm ingress

Candidate `41425de21c0e2e7bf0c48e0881cd1b0bc5926189` descends from approved `fe63d42d2743848f7933309c833577e5b204ba35`. It temporarily preserves the native route when the storm override points more than 120 degrees away toward two adjacent tall solid cells and the native approach is clear. The hold lasts 1.25 seconds or until the mech re-enters the zone.

In simulated replay 1037615 the two cells held a wall spanning 4.77 to 16.86 metres, with the mech’s feet at 5.63 metres. The approved parent swapped the native uphill route for the blocked approach. The veto recovered all 4,156 verified baseline commands, restored seven placement points and reduced damage taken by 2,176, including 557.8 storm damage. It kept every command in favorable controls 1027423 and 1037812. The solid-top check could overestimate obstruction beneath an overhang.

All 120 fresh simulated placements tied against the storm parent. The 72 campus pairs had identical wire actions and measured endpoints, so this experiment measured robustness in the directed case. The remaining 48 pairs used the four-mech format. All 23 unit tests passed. The official Docker run answered all 300 ticks within budget on the third attempt after two startup timeouts. The passing run recorded p99 of 25.4 ms.

All three Sol reviewers approved this exact SHA. Survival cited full restoration and preservation of both favorable controls. Combat cited the repaired adverse trajectory and lack of fresh false-veto harm. Validation cited the building failure and the tight guard on heading and duration. Next, look for a real activation on fresh campus seeds and check cell headroom before narrowing the geometry.
