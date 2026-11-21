# Favor evade cover against a confirmed shooter

Exact `cc352c9c7f1a4d0dbdea4fa11c09c1e524c85389` on verified `03a8f93` adjusts which rival receives the existing cover bonus. It requires repeated recent gun damage from a visible dominant rival and a current legal endpoint that blocks them. It leaves route caching, candidate moves, active dodges, and other threat scoring in place.

All 72 fresh campus placements tied (24 from 1029401, plus 16 each from 1030201, 1030301 and 1030401). All 48 four-mech placements from 1029501 tied. All 23 unit tests and 300 starter sandbox observations passed.

A raw archived screen identified 160 states with a different nearest and recently confirmed repeat shooter. Full fixed-input replay across 120 archive matches changed no plans. Of 1067 native evade calls with confirmed sources in the stage audit, 634 reused a cached route, 278 already matched the modeled source or lacked one, 141 were handling a projectile and eight failed a phase or height filter. Only six reached alternate cover geometry and none changed the goal. A controlled geometry fixture proved the route choice can switch if the endpoint conditions are present.

## Actual Sol verdicts for the exact commit

- Survival, reject for practice. The cache and endpoint geometry prevent measured improvement against the actual attacker.
- Combat, reject for practice. All fresh placements tie and the archive found no switched route to verify.
- Validation, reject for practice. Raw pressure counts do not show an executable cover choice. Find an actual timely native evade before selecting a different pressure threshold.

The next test can inspect episodes where a cached route remains active through repeated damage and there is a measured legal cover alternative before expiry.
