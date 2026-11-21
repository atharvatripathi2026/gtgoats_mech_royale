# Downward gun shot on the second physics step

Candidate `00192aa51fdef74bb6d7bfd8ad36046c9bef2511` extends approved `1d146590e77aad09e012b715e22d20770946287a`. It keeps the first-step branch and checks pitch, yaw, intercept and line again for a cooldown that expires on the second 50 ms physics step.

All 120 fresh simulated placements tied against the gun parent, including 48 four-mech games, 40 campus standard games and 32 joint and faster campus games. Joint seed 1040108 produced an additional 63 damage through six seconds at equal incoming damage, then tied placement and survival. Standard seed 1039203 took 315 less total damage and finished as the winner 2.65 seconds earlier. In archived replay 1030212 the earlier gun hit dealt 59.4 damage with equal first-three-second incoming damage. In replay 1036520 the added 45 damage preceded one lost placement point. These longer outcomes depend on later decisions and contacts.

The unit suite passed 22 tests. An official Docker rerun answered all 300 observations within 50 ms with 31.6 ms p99. The first attempt recorded three late ticks.

All three Sol reviewers approved this exact SHA. Survival cited the retained first-step branch and independently observed hits. Combat cited the fresh 63-damage hit and exact runtime check. Validation confirmed a true second-step shot in 1040108 plus a separate fresh early hit in 1039203. The next evaluation should keep measuring both near-term trades and late match outcomes.
