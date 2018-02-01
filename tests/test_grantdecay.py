"""Tests for grantdecay, stdlib unittest only."""

from __future__ import annotations

import io
import os
import unittest
from contextlib import redirect_stdout
from datetime import date

from grantdecay import cli
from grantdecay.accesslog import AccessLogError, parse_access_log
from grantdecay.decay import (
    KIND_DORMANT_PRINCIPAL,
    KIND_NARROWABLE_ROLE,
    KIND_UNGRANTED_USE,
    KIND_UNUSED_PERMISSION,
    analyze,
    build_surface,
)
from grantdecay.entitlement import EntitlementError, parse_entitlements
from grantdecay.window import DEFAULT_MIN_DAYS, Window, WindowError, is_conclusive

HERE = os.path.dirname(os.path.abspath(__file__))
SAMPLES = os.path.join(os.path.dirname(HERE), "samples")
ENT_PATH = os.path.join(SAMPLES, "entitlements.txt")
LOG_PATH = os.path.join(SAMPLES, "accesslog.txt")


def _read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


class WindowTests(unittest.TestCase):
    def test_length_is_inclusive(self):
        w = Window(date(2026, 6, 1), date(2026, 6, 1))
