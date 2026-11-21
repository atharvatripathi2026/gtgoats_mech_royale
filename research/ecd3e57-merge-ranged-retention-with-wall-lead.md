# Merge ranged retention with wall-aware mortar lead

Exact `ecd3e57e69528952a31b274e31346b0ff56cd2a0` combines parents `258d8c63654e9d24dacfa6c4c6a675e4b63b6e5f` and `8c569b43ea3dfe6a41c989f7d35a0ebe890193af`. It adds the effective ranged-arm retention code to the wall-lead tree. An earlier wall-aware hit can make a later swap eligible for retention. The full merge tree also carries the wall parent's gun behavior. [Wall-lead review](258d8c6-shorten-mortar-lead-before-a-wall.md) · [Retention review](8c569b4-retain-effective-ranged-arm.md)

Of 64 traced fresh simulated pairs, 28 placements tied against `258d8c6`, 28 against `8c569b4` lost ten points in one loss and 27 ties, and eight against verified `03a8f93` gained five points in one gain and seven ties. The verified comparison reflects the full branch. Directed 1051313 retained mortar and gained one point with 1,653.3 less incoming. The directed laser output gain and two wall-hit controls survived.

In fresh 1059427 against `8c569b4`, both selected player 2 at 50.4 seconds. The retention parent clamped a legal downward gun shot and fired, while the merge sent a lower aim and withheld fire. The merge lost ten placement points, five kills, 11 cubes and 79.9 seconds of survival. A later replay identified this as a gun-lineage difference, separate from the wall calculation. Unit and 300-tick Docker checks passed.

All three reviewers voted **revise**. They retained the directed evidence for keeping the ranged arm and pointed to the dropped downward gun command as the concrete fresh regression. Withheld. Transfer only the mortar solve onto the retention tree and replay 1059427.
