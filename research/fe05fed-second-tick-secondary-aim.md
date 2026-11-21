# Test a cooling gun while another weapon controls aim

Tested `fe05fedf2022f1f3ddfde7955d1b4e484aea7e78` against `cc7628485b7b5ea5b53f51af18baec5e624bd86a`. The extension predicts the actual aim toward the selected weapon across two physics ticks when checking whether the gun can also fire. It preserves prior movement, aim commands and other triggers.

All 24 standard campus pairs (991001–991024), 16 scaled pairs (991101–991116), and 48 four-mech pairs (991201–991206 across both maps) tied on placement. Across 141,243 fixed-input observations and 56 games, the exact variant did not change a gun trigger. An isolated fixture can activate it with deliberate geometry, and all 25 unit tests passed. The Docker rerun answered all 300 observations on time.

All three Sol reviewers voted **reject** because the arithmetic closes a hypothetical case without providing a measured gameplay benefit. Retain the gun-primary rule and spend the next tests on decisions with observed activation.
