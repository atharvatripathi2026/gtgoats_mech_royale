# Count rounds arriving within the finishing window

Tested `2dd49b0b2e105b2c3c965812d5f3c5fc1a4af287` against `489c7211da0f707e27bba0741abf487fe084871e`. The revised estimate accounts for reload, cooldown, magazine rounds and shot flight time. It changes both fight eligibility and target ranking.

| Simulated sample | Paired games | Placement points per game | Improved / tied / worse |
| --- | ---: | ---: | ---: |
| Campus squad, 961401–961424 | 24 | −0.083 | 1 / 22 / 1 |
| Independent campus squad, 962201–962216 | 16 | +0.500 | 1 / 15 / 0 |
| Independent public upgrade model, 962901–962916 | 16 | 0.000 | 0 / 16 / 0 |
| Four-mech, 961501–961506 across two maps and four scenarios | 48 | 0.000 | 0 / 48 / 0 |

In simulated seed 962212, a target switch increased damage dealt by 145.8 over the first second without changing damage taken. Later placement improved eight places. On seed 961423, the candidate kept aiming at the same lone wounded enemy but stopped engaging. It dealt zero in the first second versus 48.6 for the parent and placed three positions lower. The legacy pooled mean of +0.15 across 40 games depends on the single eight-place gain.

All 24 unit tests and 300 starter-check observations passed with a 2.7 ms replay p99.

| Sol reviewer | Practice vote | Reason |
| --- | --- | --- |
| Survival | Revise | Switching targets had a measurable benefit, while withdrawing from the lone wounded target caused a demonstrated loss. |
| Combat | Revise | The pooled gain was concentrated and the estimate changed whether to engage, despite no alternative target in the loss. |
| Validation | Revise | All public-upgrade placements and survival tied. The estimate still overcounts shots during a long torso turn. |

Test whether applying the delivery estimate only to ordering keeps the target-switch benefit while preserving the incumbent engagement decision.
