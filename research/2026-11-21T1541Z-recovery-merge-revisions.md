# Recovery merge revisions

The merge pairs [visible neighboring cubes](d861298-keep-approach-for-a-visible-neighbor-cube.md) with [rival pickup confirmation](758762f-confirm-rival-recovery-pickup.md). Each prototype had those two exact Git parents. Results below are simulated.

- `45fe9972c4ff418b24685d5ab768568ed42f711a` combined the two gates. All 172 fresh pairs tied placement. In a controlled real pickup, the rival gained two cubes while the third, observed immediately beforehand, stayed outside the rival's actual pickup radius. Hiding the third for two wire observations caused the merge to abandon the route and lose one place relative to the visible-neighbor parent. That parent resumed the approach and collected the surviving cube at t30.9. Survival, combat and validation voted **revise**.
- `d180bb570eb819b4d1c6a1b34a09db3d3ce0fcdb` consulted the short initial recovery cache for evidence of a larger pack. All 100 fresh pairs tied placement. Both independent checks reproduced the one-place loss because that cache expires 2.5 seconds after the kill, even as a selected route continues. Survival, combat and validation voted **revise**.
- `d1c1b7b722e37203cce31770e6ff08a247f5b26d` carried the maximum simultaneous pack count during the active chase. All 116 fresh pairs tied placement. This recovered the surviving cube when all three had appeared together. Two independent observation-order experiments exposed the same one-place loss when the three IDs were seen on staggered ticks and at most two were visible in any one observation. Survival, combat and validation voted **revise**.

The resulting test compares the union of distinct observed IDs across the active chase with the two-cube gain. Native close-range absence confirmation remains available.
