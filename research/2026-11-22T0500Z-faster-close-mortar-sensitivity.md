# Faster-closing opponents and the mortar-to-laser swap

Evaluator-only commit `2613427e6251f5cee9f9bf43f7c195477ceed92b` on main `ad3ffbb4e16e501790d5fbe5ca68dbd8497421d3` reduces nearby squad strafe angle from 1.1 to 0.55 radians within 75 m. Open-ground radial walking speed rises from 5.31 to 9.98 m/s. Aiming, map, schedules and pickup-before-fire order stay stock. This is simulated opponent sensitivity.

On campus 1070726, `5f0ace9121f41f8ff702c7e94f5494649c4671da` still fires the mortar and takes the same laser #10015 at 121.2 s, 0.1 s later than parent `c02206723394bcfb71d7405c25c2cac25474f0e5`. Six-second damage rises 633.60→1244.24 at zero received. Placement improves 4→5, against 8→15 in stock. Survival changes 222.55→187.70 s. All eight fresh campus squad16 pairs (1073020–1073027) tie on commands and placement.

The opening mortar payoff survives this faster closing model under pickup-first. The larger terminal gain is sensitive to opponent movement, and the prior fire-first test removed the opening payoff. [Exact candidate and original review](5f0ace9-mortar-before-laser.md)
