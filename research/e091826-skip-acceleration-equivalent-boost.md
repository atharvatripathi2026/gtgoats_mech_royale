# Conserve boost during acceleration-limited ground movement

The gameplay freeze `ba3d67a43a2fbd11ee33c386baf538f5dd8f7673` descends from sidestep parent `e0e641aeea2223f7a8dc6760188d4e2a939cd8eb`. Its exact reviewed child `e09182692b32be0272c52b7a2d52da4c7a0dd93b` corrects only the unit fixture's initial velocity. The live gameplay bytes match. In calm-ring grounded evade it omits boost when predicted walking and sprinting remain within 0.035 m across the next two physics ticks and 0.35 m/s at the endpoint. It skips emergency dodges, jets and laser-charging frames. The only direct action change is boost.

| Fresh simulated panel | Candidate | Seed start | Pairs | Placement change | Improvement / tie / regression |
|---|---|---:|---:|---:|---:|
| Standard campus | ba3d67a | 1017301 | 24 | +5 | 4 / 19 / 1 |
| Independent standard | ba3d67a | 1018001 | 16 | −1 | 4 / 9 / 3 |
| Joint hull and impact | ba3d67a | 1018101 | 16 | +2 | 2 / 12 / 2 |
| Exact independent standard | e091826 | 1018801 | 16 | −2 | 2 / 9 / 5 |
| Exact joint hull and impact | e091826 | 1018901 | 16 | +2 | 3 / 11 / 2 |
| Four-mech | ba3d67a | 1017401 | 48 | 0 | 0 / 48 / 0 |

The final exact child passed all 24 units and 300 starter observations, with p99 of 32.1 ms. In 1016011 six omissions saved 11.1 energy by 65.2 s, with under 0.035 m of path difference in the window and equal first-three-second damage. Placement fell two points. In 1016013 one omission saved 1.7 energy with the same path and weapon output in the early window and gained two points.

In joint 1018101 at 145.7 s the horizontal path matched through the first observation. But the ground tile dropped 0.0359 m and the incumbent used its held boost as a jet on the second physics tick. The vertical difference exceeded the predicted horizontal tolerance and then changed movement. That game gained four eventual points, which provided no evidence of a ground-equivalent stride at the relevant moment.

All three reviewers voted **revise**. Survival cited the real energy savings and the terrain transition. Combat cited mixed independent placement and later divergence despite locally similar motion. Validation identified the lift into an airborne tick as a reason to preserve boost near a drop. The queue received no candidate for this behavior.
