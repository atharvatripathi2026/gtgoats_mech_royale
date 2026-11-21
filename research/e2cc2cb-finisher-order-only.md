# Apply the arrival estimate only to target order

Tested `e2cc2cb3bb81fb3f39e5b349b19ef2a51931b5c1` against `489c7211da0f707e27bba0741abf487fe084871e`. This revision of [the magazine estimate](2dd49b0-ready-magazine.md) preserves the incumbent fight gate and applies the expected rounds only to the finishing priority. A 7,200-case single-target audit confirmed engagement permission parity. In the two original closed-loop replays it repaired the three-place loss and kept the eight-place gain.

| Simulated sample | Paired games | Placement points per game | Improved / tied / worse |
| --- | ---: | ---: | ---: |
| Campus squad, 963001–963016 | 16 | +0.188 | 1 / 15 / 0 |
| Independent campus squad, 963201–963216 | 16 | −0.500 | 0 / 15 / 1 |
| Independent public upgrade model, 963401–963416 | 16 | 0.000 | 0 / 16 / 0 |
| Four-mech, 963101–963106 across two maps and four scenarios | 48 | 0.000 | 0 / 48 / 0 |

In independent seed 963215, the revised policy switched from enemy 0 at 169.8 m to enemy 6 at 116.2 m. It dealt 140.4 more in the first second and took equal damage. It still survived 149.85 seconds less and placed eight positions lower. The owner winner started its first visible action change by removing 0.05 HP from a nearly defeated enemy. A cached negative sight check had kept the incumbent from selecting that contact at that tick. The first choice and the final placement should be assessed separately.

All 24 unit tests and 300 starter-check observations passed with a 3.2 ms replay p99.

| Sol reviewer | Practice vote | Reason |
| --- | --- | --- |
| Survival | Reject | The original lone-foe behavior was restored, but the remaining independent loss came from target ranking. |
| Combat | Reject | The gain did not transfer. The independent regression dealt more immediate damage and finished substantially lower. |
| Validation | Reject | Engagement parity and the motivating archived cases passed, while fresh legacy placement fell and public-upgrade results tied. |

Review how often a wounded top candidate is now visible while a cached negative sight result is still active. Test a bounded recheck only if the observation profile shows repeated, materially re-exposed targets. Keep target ranks fixed in that test.
