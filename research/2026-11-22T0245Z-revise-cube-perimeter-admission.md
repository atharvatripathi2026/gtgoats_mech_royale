# Revise cube route admission

All three reviewers voted revise on each of the following builds on `89afa91c2514fa3951271e28b1d0be8141bd20f4`. Each checks raw prism clearance for the current hull and the expected growth from nearby cubes. The 92-tape screen found four distinct pickups with confirmed approximate corridors among 3,108 sampled stalled-cube observations.

| Exact commit | Change | Simulated result that changed the decision |
| --- | --- | --- |
| `a9a33cf35159319f75264abdd31c7002d57c7c33` | Quiet cube routes across cube counts | Actual earlier cubes in 1071653 and 1071185, with placement losses of three and two. Twelve fresh campus pairs average −0.333. Twelve four-mech pairs tie. |
| `8d841e99b8d572620b63d946677fc6b39310ab4d` | First cube only | Restores the two prior losses. On 1071438 it collects the first cube and plating much earlier at tied stock placement, but loses one point and 97.6s in the scaled-hull model. Independent fresh 1071900–03 include a three-point gain in 1071901. |
| `7ab233bfa29516d4501cf14ed226c34d9a4770dc` | First cube only, measured speed at most 1m/s | Preserves the favorable pickup and four independent fresh command ties. The adverse scaled 1071438 still loses one point after delaying the same cube route by one observation. |

The adverse cube was first selected at 4.5s while the bot was moving. The speed-only rule retries it as the bot settles at 9.3s. In the favorable scaled replay, the cube is newly selected at 146.2s after the bot has already come to rest. The next version tests only a new first-cube selection from rest. [Existing weapon pickup](89afa91-reach-visible-weapon-at-legal-perimeter.md)
