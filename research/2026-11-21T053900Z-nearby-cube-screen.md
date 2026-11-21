# Reachability in the post-elimination cube replays

The previous pressure-retirement bot changed the first emitted action in 43 of 72 paired simulated campus replays. The first change in 24 pairs included a command beyond movement. Four others moved for reasons outside the transition from avoiding exposure to pursuing loot. The remaining 15 initially aimed movement at a visible cube. Two began within 15 m of the selected cube. The short screening estimate uses straight-line distance to pickup radius, top speed, and a terrain and clearance check.

- 1022118 started 14.5 m away with a legal direct ground segment. The optimistic travel bound was 0.94 s. The movement-only candidate recovered both cubes 0.5–0.6 s sooner and received zero damage in the first three seconds, down from 41.4. Both bots won.
- 1023416 started 13.2 m away with a blocked ground segment. The broader predecessor collected earlier in this replay, but the direct route fails the conservative ground test.
- 1023208 began airborne 53.4 m from its chosen cube. The broader predecessor recovered it 1.6 s sooner and gained nine placement points. This outcome motivates a separate air-route hypothesis.
- 1022117 also began airborne, 61.7 m away. Neither bot collected that cube within 12 seconds and the broader bot lost eight placement points.
- In the fresh faster joint 1024607, the new movement-only candidate triggered twice on a cube 22.3 m away. Both versions collected the two nearby cubes at +1.7 s and the next two at +4.9 s. Both took and dealt zero damage in the first six seconds. The new path eventually turned a second place into a win. That result measures trajectory sensitivity and gives no evidence of earlier pickup in this seed.

The useful next experiment is an arrival-time option under current velocity and terrain, with a separate airborne landing check and outcomes timed from the first changed action. [Prior pressure-retirement experiment](361d08c-retire-defeated-shooter-pressure.md)
