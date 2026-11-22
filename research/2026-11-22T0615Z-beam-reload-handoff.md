# Keep the rifle loaded through a same-rival beam release

Frozen research commit `f82ea28236c9967a2ff9fdc8ea8a1d448d4e19ca` on `3bf5589803723b38e740affd5e9123e083a860d4` defers a nonempty voluntary rifle reload for the observation when a charged laser releases toward the same rival the bot was engaging. The guards require a grounded stable release, a clear projected beam path and no active swap. Forced empty reload remains native. Earlier broader controls had mixed or adverse outcomes.

In simulated 1072856 the first change only removes reload at 221.1 s. Both arms land the existing 345.45-damage beam on rival #14. The candidate retains six rifle rounds and lands rifle hits earlier. First-six outgoing ties at 973.21, incoming falls 183.6→0, and placement rises 11→13 with 16.7 s longer survival. In 1071431 the same 510.3 beam lands in both arms and both first-six trades tie. The next kill takes 0.3 s longer despite a later four-point gain. In 1069732 the same 488.187 beam lands while the next rifle hit is 0.1 s later and full outcomes tie. These secondary cases expose the risk of deferring a useful reload when a rifle engagement is delayed.

Eight fresh stock campus squad16 pairs (1073400–1073407) match commands and placement. This exact SHA is ready for independent timing tests and cross-role review. It has no practice ledger entry. Full traces are local.
