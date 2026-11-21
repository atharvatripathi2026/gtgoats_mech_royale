# Defer a spacing probe against a retreating gun opponent

`ce0d05af3d57e57950eae84889c041358aefd94a` descends from `8b9f76db264c8aa33e6c70b8ef67c741cb56f60d`. It defers an optional spacing probe when the lone visible gun opponent is moving away faster than 3.5 m/s and its torso points away. The change retains observed arm samples, rewards and current arm selection. It addresses the broader rule that discarded neutral probe feedback. [Earlier probe review](17117c0-informative-feedback-for-probes.md)

In archived 1055702, a stationary hold deferred the probe and gained three placement points with both sides' first six seconds of damage unchanged. Both closing-opponent controls reproduced all 3,811 and 3,101 stock actions. The default campus diagnostic gained five points across 24 fresh pairs (+6, −1, 22 ties). The same seeds with stricter movement acknowledgement lost four points (+1, +2, −7, 21 ties). All 128 four-mech placements tied in an endpoint-only panel. The default campus panel kept full traces. All 24 units and 300 timed Docker observations passed.

In the traced strict loss 1058218, the rifle opponent really was moving and aiming away. The adaptation change at 50.2 seconds affected only movement on a native wounded-opponent flank. Incoming was zero for both sides in the next 24 seconds. Trial outgoing fell by 136.35 in that window, and the trial ultimately lost seven points, 125 seconds of survival and five cubes. The successful directed 1055702 and prospective default 1058211 both began in a stationary hold marked safe position.

- **Survival rejected.** The 24 strict pairs include a serious prospectively observed flank failure, and there is no exchange-level protection in that replay.
- **Combat voted revise.** The stationary hold results support a distinct rule, but suppressing the same probe during a flank lost too much without preventing damage.
- **Validation voted revise.** The directional sign test identifies an actual retreat, but competing native objectives change whether deferring a probe helps. The default and strict panels disagree.

Withheld. Test the stationary safe-position hold revision on new seeds in both acknowledgement modes and require the wounded-opponent flank tape to reproduce stock movement.
