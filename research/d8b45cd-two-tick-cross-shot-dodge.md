# Dodge across intersecting gun paths for one command

Candidate `d8b45cd8cc1cb71077aa77f0c40f861744a0f92c` descends from `8b9f76db264c8aa33e6c70b8ef67c741cb56f60d`. It considers a nearby second gun track at a distinct angle when the grounded bot's native line dodge still projects a hit. It changes only the current movement command when a bounded alternative clears the observed tracks in the two held physics ticks and stays on legal ground and inside the zone. Existing aim, fire and boost stay as issued. The track check can include a passing round and does not identify both shooters.

On directed 970402 the candidate avoided the native 41.4-damage gun hit inside the held command and lived 0.25 seconds longer at the same placement. In fresh 1044006 the change removed a real 62.1-damage hit during confirmed multi-shooter pressure. The bot dealt 315 more damage overall and lived 0.75 seconds longer, with equal final incoming damage, kills and placement. This was one fresh observed activation with changed endpoints.

All 124 fresh simulated placements tied. The 112 pairs against the direct parent covered 64 campus and 48 four-mech pairs. The extra 12 native campus pairs against verified `03a8f93` also tied on measured endpoints. The 24 unit tests and all 300 Docker observations passed, with timing p99 of 18.5 ms.

All three Sol reviewers approved this exact commit. Survival and validation cited the fresh and archived observed avoided hits. Combat cited the bounded one-command movement and lack of a measured downside in the initial panels. The observed cases support a practice test while the effect on overall placement remains unmeasured.
