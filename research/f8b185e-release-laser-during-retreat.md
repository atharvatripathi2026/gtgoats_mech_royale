# Release a partial laser charge during boosted evasion

All three Sol reviewers voted **reject** on `f8b185e982d1bf30d51f801b904e08253218a4dd` against squad focus. This candidate releases an aligned laser that is at least 60% charged during grounded boosted evasion below 67% health. It preserves ordinary charging and releasing outside that case.

The 20-pair owner squad panel lost 0.200 placement points per game. The 12-pair independent panel gained 0.333. Each panel had one changed placement and they canceled out. All 32 four-mech pairs tied.

On owner seed 932405 the candidate released at 175.0 seconds instead of 175.3. It restored near-full movement speed roughly 0.2 seconds earlier, at the cost of 73.71 beam damage. No extra incoming damage occurred during that initial window. It eventually lost four placement points and survived 79.25 seconds less. Validation also found a ledge fixture in which the gun led a rising target high enough that the beam missed despite the tolerance check. An independent fight changed in the opposite direction. The results do not establish that trading charge for speed improves placement.

All 24 unit tests and 300 official replay observations passed.
