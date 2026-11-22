# Cube size sensitivity in the local arena

Evaluator-only `5eb795ea50ac0594af959c64a887e238ccbe306a` applies the kit's 5% per-cube growth to actor radius, height, eye and muzzle over raw-mortar model `e720001f5ff804cf674c334a63fa40a84b6aeff2`. Both comparison arms use identical gameplay `89afa91c2514fa3951271e28b1d0be8141bd20f4` and the same squad sight policy. The evaluator passes 37 existing tests.

On fresh 1071760–67 the scaled model produces gains of seven, two and one, two losses of one, and three ties. In 1071765 the first wire change is pitch at 123.3s with the same target and movement. The two-cube radius rises 2.5→2.75m, and the muzzle rises 7→7.7m. The later 69.6-damage lightning hit in the fixed-size arm is absent in the scaled arm. These outcomes show sensitivity to hull and muzzle modeling under identical gameplay. [Opponent sight comparison](2026-11-22T0230Z-squad-firing-visibility-sensitivity.md)
