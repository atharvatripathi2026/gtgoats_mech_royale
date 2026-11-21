# Limit the post-ingress boost veto to one attempt per phase · withheld

A survival scratch on `45e7d6867c4842f7d557be98997183107390ddc1` reduced the veto to one short attempt per shrink phase and stopped it on re-exit. It retained both directed wins in native and phased simulated 1068671. The phased version took 373.43 less over six seconds but dealt 189 less, and the native version took 480.5 less and dealt 252 less.

Whole-match storm dose increased by 225 native and 218 phased. The phased case also took 72.57 more in total and finished with 72.57 less HP. Survival withheld the unfrozen scratch on those tradeoffs. Further work should confirm the actual jet ascent trigger and cross-ring trajectory before altering the boost command again. [Repeated veto review](bda1379-revise-post-ingress-boost-veto.md)
