# Wait for a pending mortar impact before swapping · withhold

In native simulated 1070485, a shell fires at 266.2s and the bot picks up a laser at 266.5s. The original shell hits three rivals for 628.69 at 267.3s in both arms. A single skipped pickup only causes a retry 0.1s later and leaves the endpoints tied. A separate diagnostic blocks five attempts over 0.4s, until the item leaves reach. It reproduces on both the archived mortar lineage and `5a920eaf7e6d485f5ee350e73775f0005d857e98`.

Both versions deal 1,357.69 and take 45 over six seconds. The retained mortar lands later group hits and adds 2,301.78 total outgoing, with 67.5 more combat incoming, 55 more storm damage and 7.8s longer survival. The simulator's composite rank rises 8→9 while the pure placement proxy falls 8→7. These are two metrics from the same stock replay.

Survival, combat and validation voted to withhold the unfrozen delay. A future rule would need pending-shell evidence available before the pickup, a physically open predicted impact, and a bounded cost for walking past the laser. [Confirmed-hit retention](5a920ea-retain-mortar-for-a-confirmed-cluster.md)
