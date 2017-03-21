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
    try:
        ent = parse_entitlements(_read(args.entitlements), args.entitlements)
    except (OSError, EntitlementError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2)
    try:
        log = parse_access_log(_read(args.accesslog), args.accesslog)
    except (OSError, AccessLogError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2)
    return ent, log


def _cmd_surface(args: argparse.Namespace) -> int:
    ent, log = _load(args)
    surfaces = build_surface(ent, log)
    for line in render_surface(surfaces, log.window):
        print(line)
    any_unused = any(s.unused for s in surfaces)
    return 1 if any_unused else 0


def _cmd_unused(args: argparse.Namespace) -> int:
    ent, log = _load(args)
    findings, conclusive = analyze(ent, log, args.min_days)
    for line in render_unused(findings, conclusive, log.window):
        print(line)
    return 1 if findings else 0


def _cmd_report(args: argparse.Namespace) -> int:
    ent, log = _load(args)
    findings, conclusive = analyze(ent, log, args.min_days)
    for line in render_report(findings, conclusive, log.window, args.min_days):
        print(line)
    return 1 if findings else 0


def _cmd_version(args: argparse.Namespace) -> int:
    print(f"grantdecay {__version__}")
    return 0


def _add_inputs(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("entitlements", help="path to the entitlement export")
    parser.add_argument("accesslog", help="path to the access log export")


def _add_min_days(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--min-days",
