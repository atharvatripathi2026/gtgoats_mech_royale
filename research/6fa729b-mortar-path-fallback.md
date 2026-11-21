# Use the gun if a mortar trajectory appears obstructed

Survival and combat voted **reject** and validation voted **revise** on `6fa729b465a186039b10148884fa135d17b5abd8` against squad focus. The patch gives an eligible gun priority if both estimated mortar paths hit terrain well before the target. Archived replay showed 14 aim changes, four withheld mortar triggers, and six restored gun triggers. All 24 owner squad, 12 independent squad and 48 four-mech placement pairs tied.

Validation found plausible bridge cases where a continuous flight approximation or the chord between its sampled points sits below the true shell path. The gate then suppresses a mortar shot that could have cleared the bridge. No fresh placement result supported this exchange. The exact patch passed 24 unit tests and all 300 official replay observations.
