# Revise the quiet rifle sweep through a clear sector

Exact `082d5dd1d3b1dd5711a2bdea6118e8aa71184f29` on `d4ac3a4e807a274906dc51b1fc4b3580a2c9f388`. The turn uses current near-range terrain samples to choose a clear direction and rechecks its proposed heading on every held command.

In simulated 1073494 stock, an earlier sighting raises six-second outgoing 291.6→486 at zero incoming and gains four placement points. Raw fire gains 267.3 early and three points. Faster-close retains the 194.4 early gain at zero incoming, yet falls from first to seventh and ends 113.1s sooner. The old adverse stock 1074561 and the cover-edge 1074392 retain all commands. All 36 fresh parent pairs tie on commands and placement. Four separately tested 3.71-reference pairs lose two total points and reproduce the parent commands. All 23 unit tests and 300 timed checks pass.

Survival, combat and validation voted **revise**. Short clear samples establish room to turn locally. The faster model still shows a downstream loss with the earlier hit. Test a single bounded scan only once there is independent evidence the newly acquired rival changes an immediate threat. [Prior rear-scan review](517b871-revise-postkill-rifle-scan.md)
