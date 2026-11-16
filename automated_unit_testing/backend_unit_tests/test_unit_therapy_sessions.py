"""
Unit Tests for Therapy Sessions & Timeline Conflict Detection (routers/therapy_sessions.py).
Tests include Positive, Negative, and Edge Cases.
"""

import unittest
from datetime import datetime, timezone
from fastapi import HTTPException
from routers.therapy_sessions import _parse_iso, _check_conflicts
from tests.fake_store import Store


class TherapyConflictUnitTests(unittest.TestCase):
    def setUp(self):
        self.center_id = "center-001"
        self.therapist_id = "therapist-01"
        self.student_id = "student-01"

        # Pre-seed Store with an existing session: 10:00 to 11:00 UTC
        self.existing_session = {
            "id": "session-existing",
            "centerId": self.center_id,
            "therapistId": self.therapist_id,
            "studentId": self.student_id,
            "scheduledAt": "2026-11-20T10:00:00Z",
            "durationMinutes": 60,
            "status": "scheduled"
        }
        self.db = Store({
            f"therapySessions/{self.existing_session['id']}": self.existing_session
        })

    # ----------------- POSITIVE TEST CASES -----------------

    def test_parse_iso_valid_utc_and_timezone(self):
        """TC-THER-01: Correctly parses valid ISO 8601 timestamps with Z or offset."""
        dt1 = _parse_iso("2026-11-20T10:00:00Z")
        self.assertEqual(dt1.year, 2026)
        self.assertEqual(dt1.hour, 10)
        self.assertEqual(dt1.tzinfo, timezone.utc)

        dt2 = _parse_iso("2026-11-20T10:00:00+00:00")
        self.assertEqual(dt2.hour, 10)

    def test_no_conflict_when_sessions_do_not_overlap(self):
        """TC-THER-02: Allows non-overlapping session later in the day without exception."""
        start = datetime(2026, 11, 20, 14, 0, tzinfo=timezone.utc)
        end = datetime(2026, 11, 20, 15, 0, tzinfo=timezone.utc)
        try:
            _check_conflicts(
                self.db,
                self.center_id,
                self.therapist_id,
                self.student_id,
                start,
                end
            )
        except HTTPException:
            self.fail("_check_conflicts should not raise when slots do not overlap")

    def test_cancelled_session_does_not_block_booking(self):
        """TC-THER-03: Cancelled sessions in the same slot do not trigger a conflict."""
        self.db.data["therapySessions/session-existing"]["status"] = "cancelled"
        start = datetime(2026, 11, 20, 10, 0, tzinfo=timezone.utc)
        end = datetime(2026, 11, 20, 11, 0, tzinfo=timezone.utc)
        try:
            _check_conflicts(
                self.db,
                self.center_id,
                self.therapist_id,
                self.student_id,
                start,
                end
            )
        except HTTPException:
            self.fail("Cancelled session should not cause conflict")

    # ----------------- NEGATIVE TEST CASES -----------------

    def test_parse_iso_invalid_string_raises_422(self):
        """TC-THER-04: Non-ISO timestamp raises 422 Unprocessable Entity."""
        with self.assertRaises(HTTPException) as cm:
            _parse_iso("not-a-valid-date")
        self.assertEqual(cm.exception.status_code, 422)

    def test_conflict_exact_therapist_overlap_raises_409(self):
        """TC-THER-05: Raises 409 Conflict when therapist already has a session in that time slot."""
        start = datetime(2026, 11, 20, 10, 15, tzinfo=timezone.utc)
        end = datetime(2026, 11, 20, 10, 45, tzinfo=timezone.utc)
        with self.assertRaises(HTTPException) as cm:
            _check_conflicts(
                self.db,
                self.center_id,
                self.therapist_id,
                "student-other",
                start,
                end
            )
        self.assertEqual(cm.exception.status_code, 409)
        self.assertIn("Therapist conflict", cm.exception.detail)

    def test_conflict_student_overlap_raises_409(self):
        """TC-THER-06: Raises 409 Conflict when student already has a session with another therapist."""
        start = datetime(2026, 11, 20, 10, 30, tzinfo=timezone.utc)
        end = datetime(2026, 11, 20, 11, 30, tzinfo=timezone.utc)
        with self.assertRaises(HTTPException) as cm:
            _check_conflicts(
                self.db,
                self.center_id,
                "therapist-different",
                self.student_id,
                start,
                end
            )
        self.assertEqual(cm.exception.status_code, 409)
        self.assertIn("Student conflict", cm.exception.detail)

    # ----------------- EDGE CASES -----------------

    def test_exclude_self_id_allows_updating_same_session(self):
        """TC-THER-07: Updating a session does not conflict with itself when exclude_id is supplied."""
        start = datetime(2026, 11, 20, 10, 0, tzinfo=timezone.utc)
        end = datetime(2026, 11, 20, 11, 0, tzinfo=timezone.utc)
        try:
            _check_conflicts(
                self.db,
                self.center_id,
                self.therapist_id,
                self.student_id,
                start,
                end,
                exclude_id="session-existing"
            )
        except HTTPException:
            self.fail("Self-updating session should be excluded from conflict check")

    def test_adjacent_sessions_boundary_condition(self):
        """TC-THER-08: Adjacent back-to-back sessions (start == existing_end) do NOT conflict."""
        # Existing session ends at 11:00 UTC. New session starts exactly at 11:00 UTC.
        start = datetime(2026, 11, 20, 11, 0, tzinfo=timezone.utc)
        end = datetime(2026, 11, 20, 12, 0, tzinfo=timezone.utc)
        try:
            _check_conflicts(
                self.db,
                self.center_id,
                self.therapist_id,
                self.student_id,
                start,
                end
            )
        except HTTPException:
            self.fail("Back-to-back adjacent sessions should not conflict")


if __name__ == "__main__":
    unittest.main()
