# Sprint rifle launch position · withheld

Combat tested a scratch aim correction on exact parent `742246aaa181b45d34e4e7ee5c6a8740e8130b35`. It projected muzzle and target one physics step for a native-authorized first rifle shot during a fast grounded sprint. Local patch SHA-256 `576db7c6de487c0be84eecbd32eec1a85fefe1d4faf1702ee508bc6dba9839f5`.

Four matched directed simulations tied on terminal placement. Public seed 1068030 lost an actual 55.89-damage hit against rival 9 at 33.1s, leaving six-second damage dealt 111.78 to 55.89 and equal incoming damage. The other three pairs produced no early or terminal improvement. Combat voted withhold before freezing a commit. Survival and validation ballots were not solicited for the unfrozen patch.

The next useful control is a native shot that demonstrably misses after the real movement integration. Reconstruct the applied motion first, and then test a projected aim change.
