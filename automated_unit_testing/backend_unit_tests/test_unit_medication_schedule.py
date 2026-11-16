"""
Unit Tests for Medication Schedule Calculation & Monitor (medication_schedule.py).
Tests include Positive, Negative, and Edge Cases.
"""

import unittest
from datetime import datetime
from medication_schedule import (
    scheduled_times,
    dose_id,
    notification_id,
    dose_is_overdue
)


class MedicationScheduleUnitTests(unittest.TestCase):
    # ----------------- POSITIVE TEST CASES -----------------

    def test_scheduled_times_parses_24h_list(self):
        """TC-MED-01: Correctly parses and standardizes list of 24h formatted dose times."""
        med = {"times": ["08:00", "14:00", "20:00"]}
        times = scheduled_times(med)
        self.assertEqual(times, ["08:00", "14:00", "20:00"])

    def test_scheduled_times_parses_12h_am_pm_list(self):
        """TC-MED-02: Correctly converts 12h AM/PM formatted times to standard 24h format."""
        med = {"times": ["08:00 AM", "02:00 PM", "08:30 PM"]}
        times = scheduled_times(med)
        self.assertEqual(times, ["08:00", "14:00", "20:30"])

    def test_scheduled_times_parses_legacy_comma_string(self):
        """TC-MED-03: Backward compatibility with legacy comma-separated string format."""
        med = {"time": "09:00, 18:00"}
        times = scheduled_times(med)
        self.assertEqual(times, ["09:00", "18:00"])

    def test_dose_id_deterministic_generation(self):
        """TC-MED-04: Deterministic dose_id generation across child, medication, date and time."""
        result_id = dose_id("student-1", "Ritalin-10mg", "2026-11-16", "08:00")
        self.assertEqual(result_id, "student-1__Ritalin-10mg__2026-11-16__0800")

    def test_notification_id_deterministic_hash(self):
        """TC-MED-05: Deterministic notification ID generation for idempotent alerting."""
        n_id1 = notification_id("parent-01", "dose-100")
        n_id2 = notification_id("parent-01", "dose-100")
        self.assertEqual(n_id1, n_id2)
        self.assertTrue(n_id1.startswith("missed-medication-"))

    def test_dose_is_overdue_true_after_grace_period(self):
        """TC-MED-06: Evaluates to True when current time exceeds scheduled time plus grace period."""
        scheduled = datetime(2026, 11, 16, 8, 0)
        # 65 minutes later (default grace period is 60 minutes)
        current = datetime(2026, 11, 16, 9, 5)
        self.assertTrue(dose_is_overdue(current, scheduled, grace_minutes=60))

    def test_dose_is_overdue_false_within_grace_period(self):
        """TC-MED-07: Evaluates to False when current time is within grace period window."""
        scheduled = datetime(2026, 11, 16, 8, 0)
        # 30 minutes later
        current = datetime(2026, 11, 16, 8, 30)
        self.assertFalse(dose_is_overdue(current, scheduled, grace_minutes=60))

    # ----------------- NEGATIVE & EDGE CASES -----------------

    def test_scheduled_times_ignores_invalid_formats(self):
        """TC-MED-08: Skips malformed strings and invalid non-time representations gracefully."""
        med = {"times": ["invalid-time", "25:99", "12:00", None, 123]}
        times = scheduled_times(med)
        self.assertEqual(times, ["12:00"])

    def test_scheduled_times_empty_or_missing(self):
        """TC-MED-09: Returns empty list if neither 'times' nor 'time' is configured."""
        self.assertEqual(scheduled_times({}), [])
        self.assertEqual(scheduled_times({"times": []}), [])
        self.assertEqual(scheduled_times({"time": ""}), [])

    def test_dose_id_sanitizes_special_characters(self):
        """TC-MED-10: Sanitizes punctuation and special characters from medication ID for clean doc keys."""
        result = dose_id("s#1", "Meds/Daily*Special!", "2026-11-16", "12:30")
        # Slash and exclamation replaced with underscore
        self.assertNotIn("/", result)
        self.assertNotIn("*", result)
        self.assertNotIn("!", result)

    def test_dose_is_overdue_exact_boundary(self):
        """TC-MED-11: Verifies exact boundary behavior at scheduled_at + grace_period."""
        scheduled = datetime(2026, 11, 16, 8, 0)
        exact_grace_end = datetime(2026, 11, 16, 9, 0)
        # now >= scheduled + 60 mins is True
        self.assertTrue(dose_is_overdue(exact_grace_end, scheduled, grace_minutes=60))


if __name__ == "__main__":
    unittest.main()
