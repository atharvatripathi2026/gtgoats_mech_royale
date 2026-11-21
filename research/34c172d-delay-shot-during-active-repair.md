# Give an active repair a short window before firing

`34c172d56c0c9fcf309e15379fccdfdd0d4f966f` is a child of verified `03a8f93fb36afa5db4a08f211d1d1aa6dcbcae8e`. It defers a ready gun for at most 0.9 seconds once per ongoing repair, after two successive own HP increases at unchanged capacity. The bot must be grounded, safe, outside evasion and tracking an established, healthy turned-away target with no observed gun or beam exposure. It retains native aim, movement and reload. Ordinary ground travel can still qualify.

| Fresh simulated panel | Seed start | Pairs | Placement change | Improved / tied / regressed |
|---|---:|---:|---:|---|
| Standard campus | 1022301 | 24 | −1 | 0 / 23 / 1 |
| Independent standard campus | 1022901 | 16 | +4 | 1 / 15 / 0 |
| Joint hull and impact | 1023001 | 16 | −1 | 0 / 15 / 1 |
| Faster joint opponent cadence | 1023101 | 16 | −7 | 0 / 15 / 1 |
| Four-mech | 1022401 | 48 | 0 | 0 / 48 / 0 |

All 23 unit tests and 300 starter observations passed, sandbox p99 29.1 ms. Fixed replay detected 29 suppressed shots across 11 of 120 matches, with the same selected target each time. Known 1014203 preserved 92.2 HP over three seconds with equal incoming, at a cost of 70.2 outgoing damage. Known 1014213 preserved 64.8 HP with equal incoming while giving up 216 outgoing. It gained one place.

Fresh fast-model 1023110 gained 42.7 HP while losing 280.8 outgoing at equal incoming across three seconds. It lost seven placement points. The only fresh standard placement gain had identical repair and damage during its first three seconds.

All three reviewers voted **reject for practice**. The repair window restores HP, but healthy, turned-away opponents can still offer productive firing windows. On these exact tests, there was no consistent advantage to taking the repair instead of the shot. The queue received no candidate.
