# Retain a sole mortar trigger during a checked rifle dodge · revise

Exact `b388f5470b85067cead684da4e6a27a9e79aa9a0` on `d6251aaff583fce5647062c16fb7a5b367710155` permits a grounded rifle-dodge override while only a ready mortar is firing. It keeps aim and fire, and checks terrain along the moved muzzle's short ballistic path.

In a staged version of the real 1069728 decision, both arms receive the same forced ready mortar and trigger. Literal arena motion avoids known round 10343 with the candidate. The mortar launches in both arms with equal velocity and clear nearby paths, with muzzle position shifted 0.14625m. This diagnostic establishes launch compatibility. The shell's eventual target hit is unmeasured.

Both directed stock controls and all 36 fresh parent pairs tie on complete commands and placement (16 stock squad, 16 standard four-mech and four independent fast-rival). Six additional comparisons against the commit-linked 3.71 reference tie placement. Across 562 archived campus tapes with repeats, 366 sole-mortar line-dodge commands yield zero legal alternate turns after masking only the trigger. An independent screen finds 13 same-command incoming rifle hits during mortar fire. The three grounded cases all retain the same contact under every sampled ±15/30/45/70° perturbation. Exact build passes 23 unit tests and 300 timed networkless observations.

All three reviewers voted **revise**. The staged protection does not demonstrate a natural mortar exchange. Short terrain clearance leaves near-hull interception and eventual impact unverified. Revisit on a live command that demonstrates both an avoided incoming round and a preserved actual mortar hit. [Merge review](d6251aa-merge-replan-dodge-with-mortar-wall-lead.md)
