# Wait one observation for an already launched finishing round

`977811b89371d1e6ff0b4a463d8a358ef45a75a1` descends from `6693026eabcde9638c74280595c348382cbbcdb6`. It confirms a one-round ammo decrease in the same gun slot, estimates arrival, and can omit one redundant trigger at the same slow, low-HP rival within the estimated arrival window. It keeps target, aim, legs and other slots unchanged on that observation. The confirmation proves launch. Lethality, ballistic clearance and the hit itself remain estimates.

| Fresh simulated panel | Seed start | Pairs | Placement change | Improvement / tie / regression |
|---|---:|---:|---:|---:|
| Standard campus | 1017101 | 24 | +5 | 2 / 21 / 1 |
| Independent standard campus | 1018201 | 16 | −6 | 0 / 13 / 3 |
| Joint hull and impact | 1018301 | 16 | −1 | 3 / 12 / 1 |
| Four-mech | 1017201 | 48 | 0 | 0 / 48 / 0 |

All 23 units and 300 starter observations passed. Sandbox p99 was 14.6 ms. Fixed replay on the same gun logic found 38 suppressed triggers across 29 of 56 matches. Thirty-three targets were killed by the native gun within 0.2 seconds. In example 963016 at 187.3 s, no hit was observed for 0.7 seconds, so the gate can omit a genuinely useful shot. In fresh joint games 1018301 and 1018305 the first six seconds of combat damage were identical between versions after the first suppression. Their placement changes were +8 and −11 respectively.

- Survival voted **reject for practice** because the savings did not repeat as directional placement and estimated arrival does not certify a hit through terrain.
- Combat voted **reject for practice** because the confirmed round savings accompanied weaker independent placement and the rule can delay fire on a miss.
- Validation voted **revise** because the ultimate placement swings did not distinguish a truly redundant finish from a delayed useful follow-up. Require actual kill evidence and a missed-shot guard before extending.

The queue received no candidate for this behavior.
