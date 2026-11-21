# Combine the exact queued gun and sight policies

The true merge `5816f38e810eaac6baf6beefa793c683f39366aa` has Git parents `367287e08745649c728a9cbee2ad2311ac781156` and `0edd2c8bddd6a1fa41093d1c39a465adb7ddeb43`. It preserves both implementations and the common 489c721 movement code.

| Simulated comparison | Pairs | Placement points per game | Improved / tied / worse |
| --- | ---: | ---: | ---: |
| Vs sight, public-upgrade campus, 966701–966716 | 16 | +0.313 | 4 / 12 / 0 |
| Vs throughput, same public-upgrade campus seeds | 16 | 0.000 | 1 / 14 / 1 |
| Vs throughput, independent legacy campus, 966801–966816 | 16 | 0.000 | 0 / 16 / 0 |
| Vs throughput, four-mech, 966901–966906 on both maps | 48 | 0.000 | 0 / 48 / 0 |

Compared with throughput alone, seed 966710 recovered mech 11 while the incumbent scanned, raising first-second damage from 52.2 to 104.4 with no incoming damage. Both guns had 12 rounds, so the event demonstrates earlier sight acquisition without a capacity interaction. Seed 966714 also recovered a target, with equal immediate damage and a later one-place loss. All 25 unit tests and 300 starter-check observations passed.

Survival approved the comparison against sight alone and voted **revise** against throughput, withholding overall approval. Combat and validation each voted **reject** for practice because no panel improved mean placement over throughput. Keep the two already queued entries separate.
