# Look beyond four occluded opponents

All three Sol reviewers voted **reject** on `95a536383ed75022c27508a8740d75b446389403` versus squad focus. It extended visibility checks from four ranked targets to at most three lower-ranked mechs the bot would engage. The fallback runs after the original options fail their visibility checks.

All 24 squad and 48 four-mech pairs tied on placement. In a crowded archived seed 921424, the candidate acquired a target in nine frames where the baseline scanned. It did not fire in those frames. A fallback can change facing and defer a reload despite no firing opportunity, so the extra visibility tests lack a demonstrated advantage.

The candidate passed 23 unit tests and all 300 official replay observations, with p99 at 2.4 ms on the test machine.
