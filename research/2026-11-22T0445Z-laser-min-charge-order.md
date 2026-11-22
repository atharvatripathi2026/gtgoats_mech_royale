# Minimum-charge laser release in the simulator

The kit describes an early trigger release as firing when minimum charge reaches 0.15 s. Stock local processing fires immediately on release and clamps power upward. Evaluator-only commit `bc24025361ce6d3613362bd3942dda96386f0592` on trusted main holds the release until minimum charge, using the torso angle of the firing step. A staged test releasing at 0.05 s and turning before the next step changed the contacted target from #1 to #2, with 151.2 damage in either arm. Target contact and line of sight were stubbed for that fixture.

On eight fresh simulated campus squad16 seeds 1072930–1072937, both evaluators used the same controller `5f0ace9121f41f8ff702c7e94f5494649c4671da`. All eight placements and seven full command traces tied. Seed 1072934 at 117.1 s produced the only natural 0.05 s release. The latch fired one additional physics step later. Both attempts missed and both arms exchanged zero damage over six seconds. Survival later changed from 186.05 s to 176.10 s, with eight placement points in both arms.

Use this model as a sensitivity test when a new policy depends on release timing. This cycle produced no gameplay candidate from the test and did not establish server timing.
