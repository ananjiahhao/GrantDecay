"""Command line interface for grantdecay.

Subcommands:

    surface    print the granted versus exercised permission surface per principal
    unused     print each unused-privilege finding, one per line
    report     print a grouped report of the four finding kinds
    version    print the package version

The surface, unused, and report commands take an entitlement export and an
access log export. They exit 1 when findings are present, 0 when clean.

Exit codes: 0 clean, 1 findings present, 2 usage error. argparse exits with 2 on
argument errors, which matches the standard.
"""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .accesslog import AccessLogError, parse_access_log
from .decay import analyze, build_surface
from .entitlement import EntitlementError, parse_entitlements
from .report import render_report, render_surface, render_unused
from .window import DEFAULT_MIN_DAYS


def _read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def _load(args: argparse.Namespace):
    """Read and parse both exports, returning (entitlements, accesslog).

    Prints a diagnostic to stderr and raises SystemExit(2) on any parse error.
    """
