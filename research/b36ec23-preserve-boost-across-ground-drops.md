# Preserve boost when the predicted stride drops off the floor

`b36ec2355056d23c95d81ca8833cc4fb3abd9fee` revises `e09182692b32be0272c52b7a2d52da4c7a0dd93b`. It leaves boost on when either held walk/sprint path would drop more than 0.025 m below the start in interpolated or coarse tile/solid ground estimates. The gameplay comparison is against `e0e641aeea2223f7a8dc6760188d4e2a939cd8eb`. Other route and weapon gates remain. [Earlier boost experiment](e091826-skip-acceleration-equivalent-boost.md)

| Fresh simulated panel | Seed start | Pairs | Placement change | Improvement / tie / regression |
|---|---:|---:|---:|---|
| Standard campus | 1019001 | 16 | −4 | 2 / 12 / 2 |
| Independent standard campus | 1019201 | 16 | +1 | 3 / 9 / 4 |
| Joint hull and impact | 1019301 | 16 | −1 | 2 / 11 / 3 |
| Four-mech | 1019101 | 48 | 0 | 0 / 48 / 0 |

All 24 unit tests and 300 starter observations passed, with sandbox p99 of 18.2 ms. Exact 1018101 preserves the boost-to-jet sequence and matches the baseline pose and energy through the earlier failure. The candidate again finished on 11 points, correcting the context behind the previous incidental four-point gain. On flat 1016013 it still saves 1.7 energy at unchanged early pose, with identical final placement. The largest fresh losses, −7 in 1019007 and −5 in 1019204, had equal first-second damage after the first omitted boost.

All three reviewers voted **reject for practice**. Survival cited the fixed terrain case and verified flat saving but weaker fresh campus placement. Combat cited the lack of repeatable placement upside despite the narrower physical rule. Validation cited the negative pooled result and the remaining uncertainty around grounding on a rise or stall. The queue received no candidate.
