# Defer expansion-induced reload during a line dodge

Exact `5733601c2d553972c20e4954f3cf64ce6916d686` descends from merged `049c97a20cde4894b94bb39b0f60e37a6406c63d`. An actual line dodge can defer the first partial top-off after a magazine expansion if remaining rounds still meet the old floor. Protection can persist through a later non-line evade and ends when the bot exits evade or encounters reload, equipment or ammo conditions that end the protection. Empty reload and upgrades retain their usual behavior.

In both joint evaluators, simulated 1032304 gets the first real extra shot at t158.5 and deals 243.41 more through three seconds at equal incoming. Its six-second outgoing falls 44.08 and both score 15. Public 1037211 added 315 outgoing over six seconds, one kill and one place. Joint 1055102 regressed five places and three kills despite 313.2 more six-second outgoing at equal incoming. Its first changed reload occurred when the loadout already tracked a rival. Quiet 1062953 stayed exact. All 84 fresh placements tied, including public16, native12, four-mech48 and linked8. All 23 units and 300 sandbox replies passed.

Survival and validation voted **revise**, combat **reject**. Withheld. The next revision separates scan before acquisition from already tracked targets.
