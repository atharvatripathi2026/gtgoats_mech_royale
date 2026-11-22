# Avoid rifle contact through the first replanning tick · queued

Exact `2e09c9b95971143dd8c5fdcc1fe829715504283c` on `f995228262f06e394a5b32ea598c908abd22d990` changes an otherwise idle grounded dodge only when current-command rifle contact is projected. It tests small turns at the existing throttle and checks the following physics tick using momentum and a full horizontal acceleration allowance. Aim, trigger and boost are preserved.

The stock directed 1069587 keeps a true 45-damage avoidance and the same six-second output. The projectile stays visible after the changed command and passes safely. Directed 1069589 restores every parent command, preventing an earlier regression that merely delayed the same round. The earlier large-turn loss in 1069100 also restores every parent command.

Simulated fresh 1069728 changes only movement at 78.5s. Through one second incoming goes 48.6→0 and outgoing 138.02→194.4. Through six seconds incoming goes 228.6→180 and outgoing 641.52→729. It survives 18.85s longer, gains one kill and one placement point, and takes 364.5 more damage over the full match. The other 15 fresh stock squad pairs (1069720–35), all 16 standard four-mech pairs (1069740–43) and all four independent phased pairs (1069780–83) tie on commands and placement. Six further pairs (1069760–65) tie on placement against the commit-linked 3.71 reference.

Survival, combat and validation approved the exact commit. It passed 23 unit tests and answered all 300 networkless sandbox observations in time. Queue entry 67 records the votes and parent. [Wide-turn review](a15eb27-revise-rifle-contact-before-replan.md) · [Small-turn review](4146867-revise-route-aligned-rifle-dodge.md)
