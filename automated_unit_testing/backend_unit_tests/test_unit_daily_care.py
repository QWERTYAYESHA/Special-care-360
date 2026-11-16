"""
TC-DC-01 to TC-DC-09
Automated unit tests for routers/daily_care.py
"""
import unittest
from unittest.mock import patch
from fastapi import HTTPException
from models.schemas import DailyCareSubmit
from routers.daily_care import submit_journal, get_journal, get_history
from tests.fake_store import Store


SAMPLE_MEALS = {
    "breakfast": {"ate": True, "notes": "Ate well"},
    "lunch": {"ate": True, "notes": "Finished plate"},
    "snack": {"ate": False, "notes": "Refused snack"},
}
SAMPLE_HYGIENE = {
    "teethBrushed": True,
    "handsWashed": True,
    "diaperAssisted": False,
    "hairCombed": True,
}
SAMPLE_MOOD = [{"slot": "morning", "mood": "happy"}, {"slot": "afternoon", "mood": "calm"}]


class DailyCareUnitTests(unittest.TestCase):

    def setUp(self):
        self.store = Store()
        self.store.collection("students").document("student-dc1").set({
            "id": "student-dc1",
            "name": "Sara Ali",
            "centerId": "center-alpha",
            "status": "active",
            "parentId": "parent-p1",
            "teacherIds": ["teacher-t1"],
            "therapistIds": [],
        })

    def _teacher_user(self, uid="teacher-t1", centerId="center-alpha"):
        return {"uid": uid, "role": "teacher", "centerId": centerId, "status": "approved"}

    def _parent_user(self, uid="parent-p1", centerId="center-alpha"):
        return {"uid": uid, "role": "parent", "centerId": centerId, "status": "approved"}

    def _therapist_user(self):
        return {"uid": "therapist-th1", "role": "therapist", "centerId": "center-alpha", "status": "approved"}

    def _make_body(self, **overrides):
        defaults = {
            "studentId": "student-dc1",
            "date": "2026-11-20",
            "meals": SAMPLE_MEALS,
            "hygiene": SAMPLE_HYGIENE,
            "moodTimeline": SAMPLE_MOOD,
            "physicalActivity": "outdoor play",
            "submittedBy": "teacher-t1",
        }
        defaults.update(overrides)
        return DailyCareSubmit(**defaults)

    # ───── TC-DC-01: submit journal success ──────────────────────────
    @patch("routers.daily_care.get_db")
    def test_submit_journal_teacher_success(self, mock_get_db):
        """TC-DC-01: Authorized teacher submits daily care journal; docId returned correctly."""
        mock_get_db.return_value = self.store
        body = self._make_body()
        res = submit_journal(body, self._teacher_user())
        self.assertEqual(res["message"], "Journal submitted successfully")
        self.assertEqual(res["docId"], "2026-11-20_student-dc1")

    # ───── TC-DC-02: therapist cannot submit ─────────────────────────
    @patch("routers.daily_care.get_db")
    def test_submit_journal_therapist_forbidden(self, mock_get_db):
        """TC-DC-02: Therapist role is not authorized to submit daily care journals (HTTP 403)."""
        mock_get_db.return_value = self.store
        body = self._make_body(submittedBy="therapist-th1")
        with self.assertRaises(HTTPException) as cm:
            submit_journal(body, self._therapist_user())
        self.assertEqual(cm.exception.status_code, 403)

    # ───── TC-DC-03: parent cannot submit ────────────────────────────
    @patch("routers.daily_care.get_db")
    def test_submit_journal_parent_forbidden(self, mock_get_db):
        """TC-DC-03: Parent role cannot submit daily care journals (HTTP 403)."""
        mock_get_db.return_value = self.store
        body = self._make_body(submittedBy="parent-p1")
        with self.assertRaises(HTTPException) as cm:
            submit_journal(body, self._parent_user())
        self.assertEqual(cm.exception.status_code, 403)

    # ───── TC-DC-04: cross-center submit blocked ─────────────────────
    @patch("routers.daily_care.get_db")
    def test_submit_journal_cross_center_forbidden(self, mock_get_db):
        """TC-DC-04: Teacher from center-beta cannot submit journal for center-alpha student."""
        mock_get_db.return_value = self.store
        body = self._make_body()
        with self.assertRaises(HTTPException) as cm:
            submit_journal(body, self._teacher_user(uid="teacher-other", centerId="center-beta"))
        self.assertEqual(cm.exception.status_code, 403)

    # ───── TC-DC-05: journal idempotent overwrite same date ──────────
    @patch("routers.daily_care.get_db")
    def test_submit_journal_overwrites_same_date(self, mock_get_db):
        """TC-DC-05: Submitting a second journal for same date+student overwrites the first."""
        mock_get_db.return_value = self.store
        body1 = self._make_body(teacherNotes="First notes")
        submit_journal(body1, self._teacher_user())
        body2 = self._make_body(teacherNotes="Updated notes")
        submit_journal(body2, self._teacher_user())
        doc = self.store.collection("dailyCareJournals").document("2026-11-20_student-dc1").get().to_dict()
        self.assertEqual(doc["teacherNotes"], "Updated notes")

    # ───── TC-DC-06: get journal found ───────────────────────────────
    @patch("routers.daily_care.get_db")
    def test_get_journal_returns_data(self, mock_get_db):
        """TC-DC-06: GET journal for existing date returns stored data with correct docId."""
        mock_get_db.return_value = self.store
        self.store.collection("dailyCareJournals").document("2026-11-20_student-dc1").set({
            "studentId": "student-dc1", "date": "2026-11-20",
            "meals": SAMPLE_MEALS, "hygiene": SAMPLE_HYGIENE,
            "moodTimeline": SAMPLE_MOOD, "physicalActivity": "outdoor play",
            "teacherNotes": "Good day",
        })
        res = get_journal("student-dc1", "2026-11-20", self._teacher_user())
        self.assertEqual(res["date"], "2026-11-20")
        self.assertEqual(res["teacherNotes"], "Good day")

    # ───── TC-DC-07: get journal not found ───────────────────────────
    @patch("routers.daily_care.get_db")
    def test_get_journal_missing_date_raises_404(self, mock_get_db):
        """TC-DC-07: GET journal for non-existent date raises HTTP 404."""
        mock_get_db.return_value = self.store
        with self.assertRaises(HTTPException) as cm:
            get_journal("student-dc1", "2026-01-01", self._teacher_user())
        self.assertEqual(cm.exception.status_code, 404)

    # ───── TC-DC-08: get history returns list ────────────────────────
    @patch("routers.daily_care.get_db")
    def test_get_history_returns_list(self, mock_get_db):
        """TC-DC-08: GET history for student returns list of journals (empty when none stored)."""
        mock_get_db.return_value = self.store
        res = get_history("student-dc1", self._teacher_user())
        self.assertIsInstance(res, list)

    # ───── TC-DC-09: parent notification dispatched ──────────────────
    @patch("routers.daily_care.get_db")
    def test_submit_journal_notification_created(self, mock_get_db):
        """TC-DC-09: Submitting a journal creates a notification document for the student's parent."""
        mock_get_db.return_value = self.store
        body = self._make_body()
        submit_journal(body, self._teacher_user())
        # Check notification collection has at least one entry for parent-p1
        notif_docs = list(self.store.collection("notifications").stream())
        parent_notifs = [
            doc.to_dict() for doc in notif_docs
            if doc.to_dict().get("recipientId") == "parent-p1"
        ]
        self.assertGreater(len(parent_notifs), 0)
        self.assertEqual(parent_notifs[0]["type"], "daily_journal")
