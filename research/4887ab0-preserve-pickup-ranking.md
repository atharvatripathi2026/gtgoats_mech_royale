# Preserve weapon ranking while preferring a first weapon

All three Sol reviewers voted **reject** on `4887ab096b23c211e9f4636514e199d11476ddeb`. This revision of [the opening equipment trial](0d18dfd-opening-equipment-without-boost.md) compares with squad focus. It only adds priority to the highest-scoring eligible pickup when the original route would choose a nonweapon target. The original favorite among weapons keeps its priority.

The exact revision reproduced all 450 baseline actions on earlier regression seed 921505. All 24 owner squad, 12 independent squad and 48 four-mech pairs tied. Two targeted older simulations confirmed earlier arming by 2.5 and 3.1 seconds, followed by earlier hostile contact in both. One placed the same and the other lost four places.

All 24 unit tests and 300 official replay observations passed. The ranking correction addressed the previous failure mechanism. The fresh placement evidence did not support entering it in practice.
