# Brake inward at the late circle boundary

All three Sol reviewers voted **reject** on `422b6d33a71f0309f5483f80016cba277c8f429a`. The candidate compared current and inward movement projections over 0.35 seconds in a small high-damage circle. It applied on grounded ground movement near the edge and skipped urgent projectile dodges.

All 20 squad, 12 independent squad and 32 four-mech paired outcome records were identical to squad focus. All 23 unit tests and all 300 official replay observations passed. Clear-ground fixtures exercised the brake and confirmed it preserved the original response when an urgent projectile or obstruction was present.

In the motivating seed 921419, both versions took 221.25 zone damage. A direct inward line failed terrain clearance. In a fixed-observation check at 381.7 seconds, a legal six-metre angled movement ray projected to 24.63 metres from the center of the 25-metre circle. The native movement projected to 25.15 metres. The straight-in brake never chose the alternate. This supports testing a short legal route along the circle edge using the actual movement command and the projected moving boundary.
