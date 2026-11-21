# Start pack memory from a visible cube at recovery admission

Exact `a311eb94e0dd1025f19494d22e403fdbb9a1c893` follows `a3db6c06a65e22d41c2b0befe8653eb1b1e3d9e0`. It carries nearby IDs from the existing 0.35-second observation cache into a new recalled route when at least one pack member is visible as the chase begins. [Earlier admission review](fe7b1c1-withhold-unqualified-admission-memory.md)

In both controlled admission simulations, the rival physically collected two cubes while the third survived. A variant used real field-of-view geometry with a controlled sensor yaw on the admission tick. The revision gained one place and one kill with the same lifetime, cube count, and damage in the first six seconds. The first emitted movement change came after the route decision changed. Native collection and complete traces were retained.

Two independent complete-depletion controls matched every parent command and outcome. In the all-absent admission control, this fixes the broader version's stale return and earlier death. In the visible-sibling admission control, both bots can still internally select a stale cube ID after two rivals divide up the pack. Their movement and placement were identical.

All 76 fresh simulated pairs matched both placement and commands, including 68 against the direct parent and eight against the 3.71 score-linked commit. All 23 unit tests and all 300 networkless sandbox replies passed. All three reviewers approved the exact commit, appended as ledger entry 54. A pack completely obscured on admission still uses the parent's observation behavior. [Gameplay commit](https://github.com/atharvatripathi2026/gtgoats_mech_royale/commit/a311eb94e0dd1025f19494d22e403fdbb9a1c893)
