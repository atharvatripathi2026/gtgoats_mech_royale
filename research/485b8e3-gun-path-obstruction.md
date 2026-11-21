# Hold gunfire when the estimated path is blocked

Survival and combat voted **reject** and validation voted **revise** on `485b8e3254929464a3a088a79a60492386382ade` against squad focus. In 24 archived matches, 83 of 2,198 ready gun decisions had an estimated terrain obstruction on the center ray, including 11 in the first 12 metres. The candidate suppresses a trigger if the center and two yaw spread samples appear obstructed ahead of the target.

| Fresh local panel | Mean placement change | Improved / tied / regressed |
| --- | ---: | ---: |
| Campus squad, 24 | +0.042 | 3 / 16 / 5 |
| Independent campus squad, 12 | −0.417 | 2 / 8 / 2 |
| Four-mech, 48 | +0.042 | 1 / 47 / 0 |

In archived seed 921409, the candidate would hold both gun triggers at 274.0 and 274.2 seconds. The baseline spent two rounds and recorded 63 damage at 274.4 seconds. No earlier shot was in flight from that firing window. Validation's ledge fixture independently showed a near-horizontal ray that appeared blocked while an upward spread sample could clear cover and still hit. The filter assumes an observed muzzle location and target distance, both of which can change before impact.

On independent seed 934809, withholding a round advanced the first hit and kill, but the subsequent route changed and placement fell from first to seventh. The largest owner gain on 934109 began with 97.2 less damage dealt in the first second after the changed trigger. Later placement swings do not measure whether the predicted obstruction was correct.

All 23 unit tests and all 300 official replay observations passed. Decision time was 1.8 ms at p99 on the replay machine.
