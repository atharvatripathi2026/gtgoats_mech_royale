# Keep a recently effective ranged arm outside lightning range

Candidate `8c569b43ea3dfe6a41c989f7d35a0ebe890193af` descends from `08f3a69150895622e401fc90c1fe60d45a26d0e8`. It vetoes a native replacement of a mortar or laser with lightning if the current arm hit a tracked rival within four seconds and observed opponents are projected to stay outside lightning range during equip. The forward mortar rule remains the same. The projection assumes current recorded motion and cannot see hidden rivals.

In directed 1051313 the retained mortar hit the selected rival 8.7 seconds before the native lightning and finished one placement point higher with 1,653.3 less total incoming. In 1040010 the retained laser hit the same rival within a second and added 1,916.71 total outgoing at 135 extra incoming in a tied win. The native lightning control 1051307 kept all 2,351 actions, and the generated forward mortar control also stayed exact.

All 88 fresh simulated placements tied. The 40 fresh campus comparisons had identical actions. The 48 four-mech pairs reported tied endpoints. The 22 unit tests and all 300 timely Docker observations passed. All three Sol reviewers approved the exact commit for the verified directed effects. Fresh play did not establish their frequency.
