# Squad firing visibility sensitivity

Evaluator-only `d04168929605267f5323fb7bec32a1bb790009a5` changes the active squad opponents' firing sight check from raster to raw world prisms. Both arms use player gameplay `ab5877abf8a5765b0aa1767cd15459e873d04a4f` and evaluator parent `e720001f5ff804cf674c334a63fa40a84b6aeff2`. The test retains local projectile motion and damage rules. An initial generic-house edit never affected the squad path and is excluded.

On eight fresh paired campus seeds 1071540–47, raw sight produces two gains of one point, two losses of one, one loss of six and three ties. In 1071540 a gun round becomes visible by 32.1s, followed by 41.4 additional damage at 39.4s. In 1071545 the first different aim arrives at 44.3s and a new visible bullet appears at 48.3s before the six-point loss. These results measure sensitivity to opponent behavior under identical gameplay.

Recorded next-attacker rays on the successful 1069728 and 1069587 controls agree across both geometries. In 1069728 the next attacker has a clear line in every sampled observation and lands 180 in both tapes. The recorded mixed escape also leaves the replacement lethal rifle lane open. Use both sight models on prospective avoidance tests. [Earlier mixed dodge](2026-11-22T0215Z-withhold-earlier-mixed-round-dodge.md)
