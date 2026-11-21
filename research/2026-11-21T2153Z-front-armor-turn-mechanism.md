# Keep an already favorable armor angle · mechanism test

Validation staged the same live incoming projectile at 3.9s of simulated seed 1067946 under the official projectile-path angle rule. Local variant `a55b8312106b33ad6b7842cfafc32c22df0bd62f` extends the queued brace `e690e7dc4625343b31ce22825aaef76ee11bfb7d` to initial front-arc impacts. Evaluator staging commit `ea532e09ae209df639a04472d396387d44690acf` places the self torso at yaw 1.0 before the shot's arrival. The existing brace turns toward 0.855 and takes 67.5 damage. The variant holds the incoming round inside the front arc at yaw 1.026 and takes 45. Both finish first. Validation treated this as a mechanism test. Formal votes were not requested.

Screen unmodified fresh traces for a native front-to-rear turn and evaluate exact alternate behavior only after confirming a genuine activation.
