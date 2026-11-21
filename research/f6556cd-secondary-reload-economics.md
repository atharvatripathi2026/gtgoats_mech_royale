# Credit sidearms with demonstrated reload coverage

Tested `f6556cda8400f2f4825a4af6951078b1847e62cb` against `367287e08745649c728a9cbee2ad2311ac781156`. A recent confirmed hit from the held sidearm while the gun is reloading can remove the extra magazine/reload upgrade credit. The exception applies only if the sidearm then wins the upgrade choice. Existing defensive scores are preserved.

All 24 owner public-upgrade campus pairs (980401–980424), 16 independent fixed-hull pairs (981501–981516), 16 independent scaled-hull pairs (981601–981616) and 48 legacy four-mech pairs (980501–980506 on both maps) tied on placement. Two out of 181 logged offers switched from a drum magazine to laser damage on fixed observations. In the controlled closed-loop 965201 replay, the different pick left the candidate with 12 rounds and the parent with 20. Neither dealt or took damage over the next ten seconds, and overall damage, kill count and placement tied. An impact during reload can be from a projectile launched earlier.

Twenty-five unit tests and 300 starter-check observations passed. All three Sol reviewers voted **reject**. Survival and validation cited the lack of outcome benefit even when the upgrade changed. Combat noted that concurrent hit evidence alone does not establish a valuable reload response. Retain the existing upgrade weighting.
