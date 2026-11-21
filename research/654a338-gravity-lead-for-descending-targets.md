# Gravity lead for a descending target

The exact candidate was `654a33801c18f59b855985ad25df361d91afc654` on the verified `03a8f93fb36afa5db4a08f211d1d1aa6dcbcae8e` gameplay baseline. Gun prediction adds gravity after two observations support downward acceleration, flight time is at least 0.24 seconds, and the vertical prediction changes by at least one metre. Landing height clamps the projection. The plane of the gun lead is still computed by the existing formula, although a new flight time can change the aim angle. Returning targets can use their jet again. Endpoint terrain samples can miss an intervening ledge.

Simulated outcomes across **120 fresh pairs** were all placement ties with identical aggregate outcomes, including 24 standard campus starting at 1023701, 16 each standard, joint, and faster joint starting at 1024101, 1024201, and 1024301, and 48 four-mech matches across six seeds from 1023801. All 23 unit tests and the 300-tick starter sandbox passed. Sandbox p99 was 18.6 ms.

Across 34 archived gun trigger frames with a visible target continuing its fall, the retrospective mean error in target altitude at impact fell from 5.32 m to 0.22 m. In directed replay 1015821, the same target at 30.6 s took 187.2 damage in the first second with the change, up from 93.6. First-three-second outgoing damage rose from 327.6 to 514.8 without receiving damage. The full-match placement points fell from 10 to 8. Directed joint replay 1020203 gained one placement point and the first changed aim had equal damage during the next three seconds.

## Actual Sol verdicts for the exact commit

- Survival, reject for practice. All 120 fresh placements tied and the two known replay placements moved in opposite directions.
- Combat, reject for practice. The replay confirms a real hit improvement in the specific geometry, and fresh matches provide no placement evidence.
- Validation, reject for practice. Keep the physical projection results for diagnostics. Skip wider use until an independently active target cohort demonstrates a sustained advantage.

The next test can sample naturally active fresh fights and measure realized damage across multiple falling targets while monitoring placement against the sealed baseline. [Prior timing experiment](35114e6-second-tick-on-verified-baseline.md)
