# Measure dodge-hop timing under interpolated squad terrain

Independent Sol validation ran the previous exact hop candidate `9a97c97ae7abaff03aba0c0656b28e72d31e4de1` against gameplay parent `2e2436e4d1ddda95aac8a86c8a18027e276da03c` on 1076469. Diagnostic evaluator `919b7da9c2a027024b06e2aa4670510aef8cb064` applies bilinear terrain and raw polygon roofs to the concrete Campus ground and surface queries. Axis walking and planner geometry use their previous checks.

The simulated jump-only intervention at 5.3 s changes placement from four to five points, versus 1→15 under coarse terrain. The six-second exchange under interpolation is 90→0 incoming and 585 outgoing in both arms. The interpolation changes the shared approach pose, from which the no-hop arm loses ground contact on the first step at a 0.033371 m gap and reaches the next observation at z 5.231 versus native z 6.141. Applying interpolation to the original coarse pose instead loses support on step two. A deliberate second-step hop works from the original pose, where the first step stays supported. The full interpolated arrival loses that option on step one.

Keep the prior revise verdict. The next controlled test is whether a lower air trajectory can avoid a traced rifle hit across both arrival poses and a second fresh seed.

[Original exact review](9a97c97-revise-dodge-hop-support.md)
