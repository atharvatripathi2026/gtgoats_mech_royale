# Revise the quiet cube-arrival sprint

All three runs use `2c9610518d914383076b47392bfd74459fd2cd65`. Survival, combat and validation voted **revise** on each of the three experimental commits below.

- `948335a805e77448af290ffebebdb5592ba3576a` advanced real pickups by one 0.1s observation. The projection capped growth despite the kit's uncapped hull size and accepted a floor drop that could turn the sprint into a jet command. Twelve fresh stock pairs gained nine points, eight independent stock lost five, and eight faster-close gained one.
- `5f0a9a9e75eb526c91eb379a5d0a86034d3c0a88` adds supported feet and uncapped sibling growth. Twelve fresh stock pairs gained two points with one gain and one loss. In simulated 1074883, the first two cubes still come one observation earlier and six-second trades tie. The next observation now picks an upgrade and changes the loot goal earlier. Placement falls 15→10 and life falls 136.25s.
- `a646dae7f359ced34be975f456598769eedb07d6` limits the move to one visible collectible cube and restores 1074883. Of 24 independent fresh matches, the two stock panels lose four and gain two total points, and faster-close gains four. The negative 1075041 and positive 1075050 both advance an upgrade so it occurs in the same command as an equipment pickup. The earlier non-threshold cube on faster 1075066 yields a later four-point gain. First-six trades tie in all three cases. The later outcome depends on the fight that follows.

All three builds passed 23 unit tests and 300 timed networkless observations. Compare the next-cube upgrade boundary to ordinary pickups, retaining exact replays with the same upgrade and equipment effects.
