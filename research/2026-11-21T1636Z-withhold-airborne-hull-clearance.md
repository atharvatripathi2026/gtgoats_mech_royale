# Test rifle clearance up to predicted hull contact

The unfrozen scratch extends the existing airborne rifle clearance rule from `2c56019db176a140a0ec30fa0d63463b396fe859`. If a terrain segment beyond the predicted target hull is blocked, it checks a shorter segmented path through nominal overlap with a moving cylinder. [Existing rifle review](2c56019-check-airborne-rifle-ray.md)

In simulated seed 1067728 a late terrain segment vetoed the first shot even though the nominal first hull entry was earlier. The scratch restored the shot one command earlier. Both 55.8-damage hits then occurred 0.1 seconds earlier, with identical one-, three- and six-second totals and terminal outcomes. The known wall rejection and original clear control were retained. All 20 fresh public-equipment comparisons 1067980–99 matched every command and placement.

Withheld before freezing or requesting votes. The replay changes timing only. Linear target motion and shorter final segments can also change terrain sample placement. Useful further evidence would show a full missed hit or a sustained disadvantage from the late segment veto.
