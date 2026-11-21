# Combine gun clearance and rear-pressure targeting

All three Sol roles declined practice for `9f14666c7fee385e9c90f50a59dc5cdac495fdcf` relative to stronger parent `88460d6e38f65a9cefaf9b24579fab25bb7f4a38`. The exact merge also has `1a4309b38967b450572c4e5f9a92b9685cda54b3` as its second parent. The two mechanisms merged cleanly.

All 44 fresh squad placements and all 48 four-mech placements tied gun clearance. Relative to rear-pressure alone, the merge gained 0.250 across 24 owner squad pairs and 0.350 across 20 independent pairs. The source and the isolated 921409 replay show it retains the gun correction, but there is no measured placement gain from adding the rear behavior to gun clearance. In the known 942020 test, local placement points were gun 11, rear 15, and merge 8. The first target or trigger divergence preceded a route change. That does not show one action caused the later result.

The exact merge passed 24 unit tests and all 300 official replay observations. Keep the individually approved parents.
