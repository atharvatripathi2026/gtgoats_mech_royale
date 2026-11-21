# Account for laser charge during the sidestep forecast

All three Sol reviewers voted **reject** on `7b007ad9f47a40f781f4c530fdc60c5763af24d6` versus standalone sidestep `e0e641aeea2223f7a8dc6760188d4e2a939cd8eb`. The predictor multiplied its target movement speed by the published charge modifier while a laser was charging. An archived analysis found 10 changed waypoints in four of 50 games, across 165 charge-and-projectile observations.

Of 24 fresh campus squad pairs, 23 tied and one lost three placement points, for a mean loss of 0.125. All 12 independent campus pairs and 48 four-mech pairs tied on placement. In the loss on seed 931412 the first divergence changed only the leg command during a charge. Both versions dealt the same laser damage at 205 seconds and took the same 90 damage by 205.4 seconds. Later trajectories differed. The forecast uses the charge visible now, which can end before the predicted crossing.

The candidate passed 24 unit tests and all 300 original replay observations.
