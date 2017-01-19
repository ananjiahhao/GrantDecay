"""The four finding kinds and the analysis that produces them.

grantdecay compares what each principal was granted against what it actually
exercised inside the observation window, then reports four kinds of finding:

    unused-permission    a principal holds a permission it never exercised.
    narrowable-role      a role confers permissions that no principal holding
                         that role ever exercised, so the role could be narrowed.
    dormant-principal    every permission a principal holds is unused; the whole
                         grant is dormant.
    ungranted-use        a principal exercised a permission it was never granted,
                         which means the entitlement export is stale or a side
                         channel exists.

The first three depend on absence of use, so they are only produced when the
window is conclusive (at least ``min_days`` long). The fourth, ungranted-use,
depends on presence of use, not absence, so it is always produced: seeing an
event that the entitlements do not explain is evidence regardless of window
length.

Every finding carries the window label so a reader can weigh the length of
observation behind it.
"""

from __future__ import annotations

from dataclasses import dataclass

from .accesslog import AccessLog
from .entitlement import Entitlements
from .window import Window, is_conclusive

KIND_UNUSED_PERMISSION = "unused-permission"
KIND_NARROWABLE_ROLE = "narrowable-role"
