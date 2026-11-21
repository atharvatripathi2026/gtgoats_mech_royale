# Pause a crate shot during an active repair · withheld

Combat tested an uncommitted crate-only trigger deferral on current `3dd401585c16880fc49703ddcb950253da6a0eb6` with narrowed patch SHA-256 `8228405f23ec18c8c7de26ccb428b17ca674707c4366814d7846d075f7aa4d2d`. It retains the old shot until a confirmed quiet recovery can gain roughly one rifle-hit worth of HP. The narrow version requires a sole loaded rifle to reduce interference from already launched ordnance.

In simulated 1068854 at 111.1s it gained 45 more HP by 112.4s while delaying the first crate hit and pickup by 1.0s. Both versions tied on placement, survival, kills, and total player trades. The broader variant sometimes delayed the trigger without gaining HP because an earlier shot was already in flight. All eight fresh public-equipment comparisons of the narrow variant tied on complete actions and placement.

Combat withheld it before a new gameplay commit. A later test needs a real approaching challenge during the added health window, or evidence the crate delay has no cost to acquisition.
