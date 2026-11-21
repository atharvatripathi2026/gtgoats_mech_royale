# Check lower-hull exposure when an eye line is blocked

Tested `27308feb4b968565fe6c656725d2a501ab0aae63` against `cc7628485b7b5ea5b53f51af18baec5e624bd86a`. If a facing opponent has a gun and its eye line is blocked, a second ray tests its size-scaled muzzle against the bot's torso. This can alter pressure and steering for a genuinely exposed lower hull.

All 56 campus placement pairs tied (24 standard 990401–990424, independent 16 standard 991301–991316 and 16 scaled 991401–991416), as did all 48 legacy four-mech pairs (990501–990506 across both maps). In the motivating 982614 replay, the rule changed the path during projectile evasion and dealt 54 more HP over three seconds. Both took the same 527.4 and finished at the same time and place. All 25 unit tests and 300 starter-check observations passed. Each reviewer voted **reject for practice** because the added sight check changed behavior without demonstrating meaningful protection or better placement.
