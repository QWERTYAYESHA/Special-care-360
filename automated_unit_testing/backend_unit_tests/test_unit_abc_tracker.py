"""
TC-ABC-01 to TC-ABC-10
Automated unit tests for routers/abc_tracker.py
"""
import unittest
from unittest.mock import patch
from fastapi import HTTPException
from models.schemas import ABCIncidentCreate
from routers.abc_tracker import log_incident, get_patterns, get_heatmap
from tests.fake_store import Store


class ABCTrackerUnitTests(unittest.TestCase):

    def setUp(self):
        self.store = Store()
        # Seed a student
        self.store.collection("students").document("student-abc1").set({
            "id": "student-abc1",
            "name": "Alex Khan",
            "centerId": "center-alpha",
            "status": "active",
            "parentId": "parent-p1",
            "teacherIds": ["teacher-t1"],
            "therapistIds": ["therapist-th1"],
        })

    def _teacher_user(self, uid="teacher-t1", centerId="center-alpha"):
        return {"uid": uid, "role": "teacher", "centerId": centerId, "status": "approved"}

    def _parent_user(self, uid="parent-p1", centerId="center-alpha"):
        return {"uid": uid, "role": "parent", "centerId": centerId, "status": "approved"}

    def _admin_user(self):
        return {"uid": "admin-1", "role": "admin", "centerId": "center-alpha", "status": "approved"}

    def _seed_incidents(self, incidents):
        """Write a list of incident dicts to fake_store."""
        for inc in incidents:
            self.store.collection("abcIncidents").document(inc["id"]).set(inc)

    # ───────────────── TC-ABC-01: log incident ───────────────────────
    @patch("routers.abc_tracker.get_db")
    def test_log_incident_success(self, mock_get_db):
        """TC-ABC-01: Authorized teacher logs an ABC incident; returns incident id."""
        mock_get_db.return_value = self.store
        body = ABCIncidentCreate(
            studentId="student-abc1",
            loggedBy="teacher-t1",
            timestamp="2026-11-20T09:30:00+00:00",
            antecedent={"tags": ["noise"], "notes": "Loud noise in hallway"},
            behavior={"tags": ["aggression"], "notes": "Hit classmate"},
            consequence={"tags": ["timeout"], "notes": "Sent to quiet room"},
            severity=4,
            durationMinutes=10,
            location="Classroom A",
        )
        res = log_incident(body, self._teacher_user())
        self.assertEqual(res["message"], "Incident logged")
        self.assertIn("id", res)
        self.assertTrue(len(res["id"]) > 0)

    # ───────────────── TC-ABC-02: role enforcement ───────────────────
    @patch("routers.abc_tracker.get_db")
    def test_log_incident_parent_role_forbidden(self, mock_get_db):
        """TC-ABC-02: Parent cannot log incidents (HTTP 403)."""
        mock_get_db.return_value = self.store
        body = ABCIncidentCreate(
            studentId="student-abc1",
            loggedBy="parent-p1",
            timestamp="2026-11-20T09:00:00+00:00",
            antecedent={"tags": ["noise"]},
            behavior={"tags": ["crying"]},
            consequence={"tags": ["comfort"]},
            severity=2,
            durationMinutes=5,
            location="Hallway",
        )
        with self.assertRaises(HTTPException) as cm:
            log_incident(body, self._parent_user())
        self.assertEqual(cm.exception.status_code, 403)

    # ───────────────── TC-ABC-03: cross-center blocked ───────────────
    @patch("routers.abc_tracker.get_db")
    def test_log_incident_cross_center_forbidden(self, mock_get_db):
        """TC-ABC-03: Teacher from center-beta cannot log incident for center-alpha student."""
        mock_get_db.return_value = self.store
        body = ABCIncidentCreate(
            studentId="student-abc1",
            loggedBy="teacher-other",
            timestamp="2026-11-20T10:00:00+00:00",
            antecedent={"tags": ["none"]},
            behavior={"tags": ["tantrum"]},
            consequence={"tags": ["redirection"]},
            severity=1,
            durationMinutes=3,
            location="Playground",
        )
        with self.assertRaises(HTTPException) as cm:
            log_incident(body, self._teacher_user(uid="teacher-other", centerId="center-beta"))
        self.assertEqual(cm.exception.status_code, 403)

    # ───────────────── TC-ABC-04: pattern empty student ──────────────
    @patch("routers.abc_tracker.get_db")
    def test_get_patterns_empty_data_returns_zeroes(self, mock_get_db):
        """TC-ABC-04: Pattern analysis on student with no incidents returns zeroed structure."""
        mock_get_db.return_value = self.store
        res = get_patterns("student-abc1", self._teacher_user())
        self.assertEqual(res["totalIncidents"], 0)
        self.assertEqual(res["avgSeverity"], 0)
        self.assertEqual(res["topAntecedents"], [])
        self.assertEqual(res["topBehaviors"], [])
        self.assertEqual(res["insights"], [])

    # ───────────────── TC-ABC-05: top antecedents counted correctly ──
    @patch("routers.abc_tracker.get_db")
    def test_get_patterns_counts_top_antecedents(self, mock_get_db):
        """TC-ABC-05: Pattern analysis ranks antecedent tags by incident count correctly."""
        mock_get_db.return_value = self.store
        incidents = [
            {"id": f"inc-{i}", "studentId": "student-abc1",
             "antecedent": {"tags": ["noise", "crowd"]},
             "behavior": {"tags": ["aggression"]},
             "consequence": {"tags": ["timeout"]},
             "severity": 3, "timestamp": "2026-11-20T09:00:00+00:00"}
            for i in range(3)
        ]
        incidents.append({
            "id": "inc-extra", "studentId": "student-abc1",
            "antecedent": {"tags": ["noise"]},
            "behavior": {"tags": ["crying"]},
            "consequence": {"tags": ["comfort"]},
            "severity": 2, "timestamp": "2026-11-20T10:00:00+00:00",
        })
        self._seed_incidents(incidents)
        res = get_patterns("student-abc1", self._teacher_user())
        # 'noise' appeared in all 4, 'crowd' appeared in 3
        top_tags = [item["tag"] for item in res["topAntecedents"]]
        self.assertIn("noise", top_tags)
        self.assertEqual(res["totalIncidents"], 4)

    # ───────────────── TC-ABC-06: average severity ───────────────────
    @patch("routers.abc_tracker.get_db")
    def test_get_patterns_avg_severity_correct(self, mock_get_db):
        """TC-ABC-06: Average severity computed correctly across incidents with varying levels."""
        mock_get_db.return_value = self.store
        incidents = [
            {"id": "inc-s1", "studentId": "student-abc1",
             "antecedent": {"tags": []}, "behavior": {"tags": []}, "consequence": {"tags": []},
             "severity": 2, "timestamp": "2026-11-20T09:00:00+00:00"},
            {"id": "inc-s2", "studentId": "student-abc1",
             "antecedent": {"tags": []}, "behavior": {"tags": []}, "consequence": {"tags": []},
             "severity": 4, "timestamp": "2026-11-20T10:00:00+00:00"},
        ]
        self._seed_incidents(incidents)
        res = get_patterns("student-abc1", self._teacher_user())
        self.assertEqual(res["avgSeverity"], 3.0)

    # ───────────────── TC-ABC-07: peak hours ─────────────────────────
    @patch("routers.abc_tracker.get_db")
    def test_get_patterns_peak_hours_detected(self, mock_get_db):
        """TC-ABC-07: Peak hours correctly extracted from ISO timestamps (3 incidents at 09:xx)."""
        mock_get_db.return_value = self.store
        incidents = [
            {"id": f"inc-h{i}", "studentId": "student-abc1",
             "antecedent": {"tags": []}, "behavior": {"tags": []}, "consequence": {"tags": []},
             "severity": 3, "timestamp": "2026-11-20T09:15:00+00:00"}
            for i in range(3)
        ]
        self._seed_incidents(incidents)
        res = get_patterns("student-abc1", self._teacher_user())
        hours = [entry["hour"] for entry in res["peakHours"]]
        self.assertIn(9, hours)

    # ───────────────── TC-ABC-08: heatmap shape ──────────────────────
    @patch("routers.abc_tracker.get_db")
    def test_get_heatmap_returns_complete_grid(self, mock_get_db):
        """TC-ABC-08: Heatmap returns exactly 35 cells (7 days × 5 severity levels)."""
        mock_get_db.return_value = self.store
        res = get_heatmap("student-abc1", self._teacher_user())
        self.assertEqual(len(res), 35)
        days_in_result = {item["day"] for item in res}
        self.assertEqual(days_in_result, {"Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"})

    # ───────────────── TC-ABC-09: heatmap counts incident correctly ──
    @patch("routers.abc_tracker.get_db")
    def test_get_heatmap_counts_incident_on_correct_day(self, mock_get_db):
        """TC-ABC-09: Heatmap places incident with known weekday (Thursday) and severity 5 correctly."""
        mock_get_db.return_value = self.store
        # 2026-11-19 is a Thursday
        self.store.collection("abcIncidents").document("inc-thu").set({
            "id": "inc-thu", "studentId": "student-abc1",
            "antecedent": {"tags": []}, "behavior": {"tags": []}, "consequence": {"tags": []},
            "severity": 5, "timestamp": "2026-11-19T14:00:00+00:00",
            "createdAt": "2026-11-19T14:00:00+00:00",
        })
        res = get_heatmap("student-abc1", self._teacher_user())
        thu_sev5 = next(r for r in res if r["day"] == "Thu" and r["severity"] == 5)
        self.assertEqual(thu_sev5["count"], 1)

    # ───────────────── TC-ABC-10: high severity insight ──────────────
    @patch("routers.abc_tracker.get_db")
    def test_get_patterns_high_severity_generates_insight(self, mock_get_db):
        """TC-ABC-10: When avg severity ≥ 3.5, an intervention plan review insight is generated."""
        mock_get_db.return_value = self.store
        incidents = [
            {"id": f"inc-hs{i}", "studentId": "student-abc1",
             "antecedent": {"tags": []}, "behavior": {"tags": []}, "consequence": {"tags": []},
             "severity": 5, "timestamp": "2026-11-20T09:00:00+00:00"}
            for i in range(3)
        ]
        self._seed_incidents(incidents)
        res = get_patterns("student-abc1", self._teacher_user())
        self.assertTrue(any("intervention" in i.lower() for i in res["insights"]))
