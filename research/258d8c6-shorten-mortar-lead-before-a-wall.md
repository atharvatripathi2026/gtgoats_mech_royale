# Shorten mortar lead before a broad wall

Exact `258d8c63654e9d24dacfa6c4c6a675e4b63b6e5f` descends from `79ae4b2c4a4c6ecba435fb3596dc2c7e240aec61`. When a moving ground target's projected center and both flanks meet solid geometry, the mortar solve can aim closer to its predicted stopping point. An earlier through-cover lob screen found no viable arc in 112 archived games. This variant retains target selection and changes the mortar aim solution, which can affect weapon alignment and trigger timing. A glancing target can keep moving along the wall faster than the stop estimate predicts. [Mortar parent](79ae4b2-mortar-with-crossing-dodge.md)

Of 88 fresh simulated pairs, 87 placements tied and one improved. In four-mech campus rotation 1058622, an aim-only change landed a 117.63-damage hit on the selected player that the parent missed. The trial killed that player and gained one placement point at equal incoming and survival. The 16 parent campus comparisons all tied on placement. Fresh 1058603 and 1058608 gained 738.13 and 499.17 total outgoing, respectively, at equal incoming and survival. The other 63 four-mech pairs and eight traced campus comparisons against verified `03a8f93` tied on placement.

In directed fast 1051706, the same-target mortar changed from 94.74 splash to 300 direct and 204.38 splash on the same impact. Both sides took zero incoming in three seconds. The trial gained six placement points. In standard 1058104 it added 686.22 actual early damage at equal incoming in a tied win. A changed launch in 1051601 still missed and tied. These are simulated outcomes.

All three Sol roles approved the exact commit. All 24 unit tests and all 300 networkless Docker observations passed on time with 1.8 ms p99. The exact commit is ledger entry 30. [Practice ledger](../queue.json)

A six-frame geometry screen for a follow-up checked where the two outside rays first hit. Some effective replays began with a side ray already blocked, including 1053309. The side-ray timing alone cannot recover a reliable common wall normal in those cases. Retain the observed positive clips as controls before testing tangential carry.
