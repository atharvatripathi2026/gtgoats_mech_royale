# Align a partially charged laser when the gun cannot fire

Tested `f975c196cadfbb8311bd5fc1aef14d937de60d30` against `8b9f76db264c8aa33e6c70b8ef67c741cb56f60d`. The trial shifts aim from a gun that will fail alignment to a ready alignment for an already charging laser. It keeps the release threshold and the incumbent's usable gun shots.

All 24 owner public-upgrade campus pairs (980201–980224), 16 independent fixed-hull pairs (981701–981716), 16 independent scaled-hull pairs (981801–981816), and 48 legacy four-mech pairs (980301–980306 on both maps) tied on placement. Rehydrating 64 archived games produced one changed aim at 134.1 seconds on 971402, with both versions holding the same trigger. A shorter aim path can be valid without discharging sooner. Different orientation may still affect later firing and sight.

Twenty-four unit tests and 300 starter-check observations passed. All three Sol reviewers voted **reject**. Combat reported only the single aim-only activation in the archive. Survival cited the absence of placement benefit and possible future gun realignment. Validation found no fresh evidence to prioritize this precise mechanism. Use the separate cooldown-timing experiment to look for recoverable gun triggers.
