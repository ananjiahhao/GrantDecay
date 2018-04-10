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
        self.assertEqual(w.length_days, 1)
        w2 = Window(date(2026, 6, 1), date(2026, 7, 1))
        self.assertEqual(w2.length_days, 31)

    def test_start_after_end_rejected(self):
        with self.assertRaises(WindowError):
            Window(date(2026, 7, 1), date(2026, 6, 1))

    def test_contains_endpoints(self):
        w = Window(date(2026, 6, 1), date(2026, 6, 30))
        self.assertTrue(w.contains(date(2026, 6, 1)))
        self.assertTrue(w.contains(date(2026, 6, 30)))
        self.assertFalse(w.contains(date(2026, 5, 31)))
        self.assertFalse(w.contains(date(2026, 7, 1)))

    def test_conclusiveness_threshold(self):
        short = Window(date(2026, 6, 1), date(2026, 6, 10))
        self.assertFalse(is_conclusive(short, DEFAULT_MIN_DAYS))
        long = Window(date(2026, 6, 1), date(2026, 7, 1))
        self.assertTrue(is_conclusive(long, DEFAULT_MIN_DAYS))


class EntitlementTests(unittest.TestCase):
    def test_role_expansion_unions_permissions(self):
        ent = parse_entitlements(
            "role a p1 p2\nrole a p2 p3\ngrant u a\n"
        )
        self.assertEqual(
            ent.effective_permissions("u"), ("p1", "p2", "p3")
        )

    def test_multiple_roles_union(self):
        ent = parse_entitlements(
            "role a p1\nrole b p2\ngrant u a b\n"
        )
        self.assertEqual(ent.effective_permissions("u"), ("p1", "p2"))

    def test_unknown_record_kind_rejected(self):
        with self.assertRaises(EntitlementError):
            parse_entitlements("frob x y\n")

    def test_grant_of_undeclared_role_rejected(self):
        with self.assertRaises(EntitlementError):
            parse_entitlements("grant u missing\n")

    def test_double_grant_rejected(self):
        with self.assertRaises(EntitlementError):
            parse_entitlements("role a p1\ngrant u a\ngrant u a\n")

    def test_comments_and_blanks_ignored(self):
        ent = parse_entitlements("# c\n\nrole a p1\ngrant u a\n")
        self.assertEqual(ent.principals(), ("u",))


class AccessLogTests(unittest.TestCase):
    def test_missing_window_rejected(self):
        with self.assertRaises(AccessLogError):
            parse_access_log("2026-06-01 u p\n")

    def test_event_before_window_header_rejected(self):
        with self.assertRaises(AccessLogError):
            parse_access_log("2026-06-01 u p\nwindow 2026-06-01 2026-07-01\n")

    def test_event_outside_window_rejected(self):
        text = "window 2026-06-01 2026-06-30\n2026-07-05 u p\n"
        with self.assertRaises(AccessLogError):
            parse_access_log(text)

    def test_counts_accumulate(self):
        text = (
            "window 2026-06-01 2026-07-01\n"
            "2026-06-02 u p\n2026-06-03 u p\n"
        )
        log = parse_access_log(text)
        self.assertEqual(log.count("u", "p"), 2)

    def test_bad_date_rejected(self):
        with self.assertRaises(AccessLogError):
            parse_access_log("window 2026-13-01 2026-07-01\n")


class SurfaceTests(unittest.TestCase):
    def setUp(self):
        self.ent = parse_entitlements(_read(ENT_PATH), ENT_PATH)
        self.log = parse_access_log(_read(LOG_PATH), LOG_PATH)

    def test_surface_counts(self):
        surfaces = {s.principal: s for s in build_surface(self.ent, self.log)}
        web = surfaces["svc-web"]
        # granted five, exercised four (rollback unused).
        self.assertEqual(len(web.granted), 5)
        self.assertEqual(len(web.exercised), 4)
        self.assertEqual(web.unused, ("deploy:rollback",))

    def test_dormant_principal_has_zero_exercised(self):
        surfaces = {s.principal: s for s in build_surface(self.ent, self.log)}
        self.assertEqual(surfaces["svc-batch"].exercised, ())


class AnalyzeTests(unittest.TestCase):
    def setUp(self):
        self.ent = parse_entitlements(_read(ENT_PATH), ENT_PATH)
        self.log = parse_access_log(_read(LOG_PATH), LOG_PATH)

    def test_all_four_kinds_present(self):
        findings, conclusive = analyze(self.ent, self.log, DEFAULT_MIN_DAYS)
        self.assertTrue(conclusive)
        kinds = {f.kind for f in findings}
        self.assertIn(KIND_UNUSED_PERMISSION, kinds)
        self.assertIn(KIND_NARROWABLE_ROLE, kinds)
        self.assertIn(KIND_DORMANT_PRINCIPAL, kinds)
        self.assertIn(KIND_UNGRANTED_USE, kinds)

    def test_dormant_principal_identified(self):
        findings, _ = analyze(self.ent, self.log, DEFAULT_MIN_DAYS)
        dormant = [f for f in findings if f.kind == KIND_DORMANT_PRINCIPAL]
        self.assertEqual([f.principal for f in dormant], ["svc-batch"])

    def test_narrowable_role_is_deploy_rollback(self):
        findings, _ = analyze(self.ent, self.log, DEFAULT_MIN_DAYS)
        narrow = [f for f in findings if f.kind == KIND_NARROWABLE_ROLE]
        self.assertEqual(len(narrow), 1)
        self.assertEqual(narrow[0].role, "deploy")
        self.assertEqual(narrow[0].permissions, ("deploy:rollback",))

    def test_ungranted_use_is_repo_read(self):
        findings, _ = analyze(self.ent, self.log, DEFAULT_MIN_DAYS)
        ung = [f for f in findings if f.kind == KIND_UNGRANTED_USE]
        self.assertEqual(len(ung), 1)
        self.assertEqual(ung[0].principal, "svc-oncall")
        self.assertEqual(ung[0].permissions, ("repo:read",))

    def test_short_window_suppresses_absence_findings(self):
        short_log = parse_access_log(
            "window 2026-06-01 2026-06-05\n2026-06-02 svc-oncall repo:read\n"
        )
        findings, conclusive = analyze(self.ent, short_log, DEFAULT_MIN_DAYS)
        self.assertFalse(conclusive)
        # Only ungranted-use survives on a short window.
        self.assertTrue(all(f.kind == KIND_UNGRANTED_USE for f in findings))

    def test_findings_are_sorted_deterministically(self):
        f1, _ = analyze(self.ent, self.log, DEFAULT_MIN_DAYS)
        f2, _ = analyze(self.ent, self.log, DEFAULT_MIN_DAYS)
        self.assertEqual([f.sort_key() for f in f1], [f.sort_key() for f in f2])


class CliTests(unittest.TestCase):
    def _run(self, argv):
        buf = io.StringIO()
