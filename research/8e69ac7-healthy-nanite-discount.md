# Discount repair upgrades when the hull is nearly full

Tested `8e69ac778f451580e5b21049d1b0c6575ed67620` against `489c7211da0f707e27bba0741abf487fe084871e`. Healthy mechs inside the circle and without recent directed damage discounted the long-term benefit of nanites in pre-endgame offers.

| Simulated sample | Pairs | Placement points per game | Improved / tied / worse |
| --- | ---: | ---: | ---: |
| Public-upgrade campus, 964201–964224 | 24 | −0.625 | 0 / 20 / 4 |
| Independent public-upgrade campus, 965001–965016 | 16 | −0.375 | 0 / 14 / 2 |
| Four-mech legacy, 964301–964306 on both maps | 48 | 0.000 | 0 / 48 / 0 |

Four owner losses traded nanites for servos at full HP. In independent seeds 965008 and 965010, swapping to jets and capacitor lost two and four places respectively. Both had identical immediate damage. A known replay where armor reduced two first hits by a total of 7.2 HP tied on placement. Momentary health and contact described the offer context without measuring later exposure or repair opportunity.

Twenty-three unit tests and 300 starter-check observations passed. The legacy four-mech model offers no nanites in this policy comparison.

All three Sol reviewers voted **reject**. Survival cited six regression games without a placement gain. Combat found that current fullness did not establish the long-run value of substituting speed or energy. Validation noted that the healthy-state guard reproduced on fixed observations but both public-upgrade panels declined. Keep the incumbent repair weighting.
