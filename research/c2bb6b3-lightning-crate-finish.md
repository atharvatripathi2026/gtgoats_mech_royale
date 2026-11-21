# Let lightning finish a crate with one shot

Combat and survival voted **reject** for practice on `c2bb6b30d1500b48463569f06c62388af40e8ba4` against squad focus `c1456b52088811a77a41473c50c4c70faa81d2e4`. Validation voted **revise**. The new rule skips firing the gun at a selected crate when a ready lightning arc looks lethal and an opponent is nearby.

All 24 squad and 64 four-mech pairs produced identical outcome ledgers. A targeted replay of seed 934057 confirmed one case where the change saved one gun round and the arc destroyed the crate. Placement stayed 10th. Validation constructed a ledge case in which the crate was visible to the bot's aim solver but cover blocked the simulator's actual arc from the muzzle to the crate center. The rule suppressed the gun in that case and lost its backup shot.

The candidate passed 24 unit tests and all 300 official replay observations. A further variant would need to check the actual arc path. The rarity of the useful case makes broader improvements to target selection a better use of the next experiment.
