# Step toward a safely reachable crate during a reload

Tested `73c16456885359d2d20bede899ce4c7f7e2d8008` against `8b9f76db264c8aa33e6c70b8ef67c741cb56f60d`. It changes legs only during an otherwise idle reload, with a nearby safe aligned crate and no close opponent. It preserves the selected crate and the weapon commands.

All 24 owner pairs (990201–990224) and 16 scaled pairs (991601–991616) tied on placement. The independent standard panel (991501–991516) gained ten total points, two gains and 14 ties. Legacy four-mech (990301–990306 across both maps) tied 48/48. In independent 991516 the same crate was destroyed at the same time, but the movement secured the first cube and a later pair of cubes 0.2 seconds earlier. The other winner, 991508, reached its next cube 3.8 seconds later, so its placement gain cannot be credited to faster farming. The known replay 970416 picked up the cubes 0.4 seconds sooner at equal placement.

The exact variant passed 23 unit tests and 300 starter-check observations. The active-charge guard read the visible enemy field rather than numeric self-weapon charge. Combat and survival voted **revise** to check the correct field. Validation voted **approve for practice** on the paired evidence and the existing cooldown protection. Withhold this version and test the corrected data-field variant.
