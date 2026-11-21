# Angle briefly toward cover during a sole-gun reload

Tested `9a3c96539e86a04c12037033aea999624974d208` against `367287e08745649c728a9cbee2ad2311ac781156`. The variant changes only the leg command when the sole gun is reloading and a nearby reachable point appears more occluded. It leaves aim, fire and immediate projectile dodges to the existing controller.

| Simulated sample | Pairs | Placement points per game | Improved / tied / worse |
| --- | ---: | ---: | ---: |
| Legacy campus, 970201–970224 | 24 | 0.000 | 0 / 24 / 0 |
| Independent legacy campus, 971001–971016 | 16 | −0.375 | 0 / 15 / 1 |
| Independent public-upgrade campus, 971101–971116 | 16 | −0.188 | 0 / 15 / 1 |
| Legacy four-mech, 970301–970306, both maps | 48 | −0.021 | 0 / 47 / 1 |

In the motivating seed 965705, the predicted path endpoint was 4.37 m from the actual position 0.8 seconds later. Four new projectile decisions replaced the predicted cover path; incoming damage rose from 135 to 225 HP in the first 0.8 seconds. Independent seed 971008 took 62.5 more in the first second after the legs redirected and eventually lost six places. An isolated overhead obstruction also blocks the eye-to-eye ray while leaving the body-center shot open. All 24 unit tests and 300 starter-check observations passed.

All three Sol reviewers voted **reject**. Survival cited the immediate loss in the motivating case and the displaced trajectory. Combat cited independent losses in both arena models and no placement gains. Validation identified an immediate holdout loss and the eye-ray geometry limitation. Any revisit should measure body exposure across the actual short trajectory.
