# Faster quiet sensor sweep

Survival and validation voted **revise** and combat voted **reject** on `e2dedc655c297db0cbeda6f234a7286316ece84b` against squad focus. It changes the default quiet sweep from about 8.0 seconds to 4.59 seconds, with the same angle amplitude and the existing combat, sound, and recent-hit aim choices.

The 24 owner squad pairs gained 1.375 points per match (11 improved, eight tied, five worse). The 12 independent squad pairs lost 1.167 (three improved, five tied, four worse). Forty-eight four-mech pairs gained 0.042. The simulated population result is uncertain across panels. All 23 unit tests and 300 official replay actions passed.

On independent seed 952803 the faster torso initially protected the mech from the rear damage multiplier. By 4.5 seconds the baseline had briefly seen pickup 8008, and the candidate's sweep had missed it. The baseline pursued loot while the candidate moved to shelter. The faster candidate died at 67.2 seconds and went from 15 to three placement points. An owner win first saw an opponent 0.4 seconds earlier and then changed several downstream interactions. Each replay motivates preserving the opening scan until the first circle closes from its initial hold and testing later observations separately.
