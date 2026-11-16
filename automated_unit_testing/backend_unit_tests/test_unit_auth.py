"""
Unit Tests for Authentication and Identity Management Module (auth.py).
Tests include Positive, Negative, and Edge Cases.
"""

import unittest
from unittest.mock import patch, MagicMock
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

import middleware.auth_middleware as authentication
from routers.auth import router as auth_router
from tests.fake_store import Store


class AuthUnitTests(unittest.TestCase):
    def setUp(self):
        self.app = FastAPI()
        self.app.include_router(auth_router)
        self.client = TestClient(self.app, raise_server_exceptions=False)
        self.db = Store({
            "centers/center-001": {"centerId": "center-001", "name": "Primary Center"},
            "users/admin-01": {"uid": "admin-01", "role": "admin", "status": "approved", "centerId": "center-001", "email": "admin@center.org"},
            "users/staff-01": {"uid": "staff-01", "role": "teacher", "status": "approved", "centerId": "center-001", "email": "staff@center.org"}
        })

        self.mock_user = {"uid": "admin-01", "role": "admin", "status": "approved", "centerId": "center-001", "email": "admin@center.org"}
        self.mock_identity = {"uid": "new-user-01", "email": "newuser@test.org"}

        # Patch get_db across auth router
        self.patch_db = patch("routers.auth.get_db", return_value=self.db)
        self.patch_db.start()
        self.addCleanup(self.patch_db.stop)

    # ----------------- POSITIVE TEST CASES -----------------

    def test_register_staff_success(self):
        """TC-AUTH-01: Valid registration request should record pending registration with 200 OK."""
        self.app.dependency_overrides[authentication.get_verified_identity] = lambda: self.mock_identity
        payload = {
            "name": "Jane Teacher",
            "email": "jane@center.org",
            "password": "ValidPassword123!",
            "role": "teacher",
            "centerId": "center-001"
        }
        response = self.client.post("/api/auth/register", json=payload)
        self.app.dependency_overrides.clear()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "pending")
        self.assertIn("pending_registrations/jane@center_org", self.db.data)
        saved = self.db.data["pending_registrations/jane@center_org"]
        self.assertEqual(saved["role"], "teacher")
        self.assertEqual(saved["centerId"], "center-001")

    def test_create_user_profile_success(self):
        """TC-AUTH-02: Authenticated user can initialize their profile with pending status."""
        self.app.dependency_overrides[authentication.get_verified_identity] = lambda: self.mock_identity
        payload = {
            "uid": "new-user-01",
            "name": "New Therapist",
            "role": "therapist",
            "centerId": "center-001"
        }
        response = self.client.post("/api/auth/profile", json=payload)
        self.app.dependency_overrides.clear()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "pending")
        self.assertIn("users/new-user-01", self.db.data)
        saved = self.db.data["users/new-user-01"]
        self.assertEqual(saved["role"], "therapist")
        self.assertEqual(saved["status"], "pending")

    def test_get_me_profile_success(self):
        """TC-AUTH-03: Authenticated active user can retrieve their own profile."""
        self.app.dependency_overrides[authentication.get_current_user] = lambda: self.mock_user
        response = self.client.get("/api/auth/me")
        self.app.dependency_overrides.clear()

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["uid"], "admin-01")
        self.assertEqual(data["role"], "admin")
        self.assertEqual(data["centerId"], "center-001")

    # ----------------- NEGATIVE TEST CASES -----------------

    def test_register_invalid_role_fails(self):
        """TC-AUTH-04: Registration with unauthorized or fictitious role should return 400 Bad Request."""
        self.app.dependency_overrides[authentication.get_verified_identity] = lambda: self.mock_identity
        payload = {
            "name": "Hacker",
            "email": "hacker@evil.org",
            "password": "Password123!",
            "role": "superadmin",
            "centerId": "center-001"
        }
        response = self.client.post("/api/auth/register", json=payload)
        self.app.dependency_overrides.clear()

        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid role", response.text)

    def test_register_nonexistent_center_fails(self):
        """TC-AUTH-05: Registration with unknown center ID should return 404 Not Found."""
        self.app.dependency_overrides[authentication.get_verified_identity] = lambda: self.mock_identity
        payload = {
            "name": "Ghost",
            "email": "ghost@nowhere.org",
            "password": "Password123!",
            "role": "teacher",
            "centerId": "center-999-invalid"
        }
        response = self.client.post("/api/auth/register", json=payload)
        self.app.dependency_overrides.clear()

        self.assertEqual(response.status_code, 404)
        self.assertIn("Unknown centerId", response.text)

    def test_create_profile_already_exists_fails(self):
        """TC-AUTH-06: Profile creation fails with 409 Conflict if profile already exists."""
        self.app.dependency_overrides[authentication.get_verified_identity] = lambda: {"uid": "admin-01", "email": "admin@center.org"}
        payload = {
            "uid": "admin-01",
            "name": "Overwriting Admin",
            "role": "admin",
            "centerId": "center-001"
        }
        response = self.client.post("/api/auth/profile", json=payload)
        self.app.dependency_overrides.clear()

        self.assertEqual(response.status_code, 409)
        self.assertIn("Profile already exists", response.text)

    def test_create_profile_uid_mismatch_forbidden(self):
        """TC-AUTH-07: Body UID mismatching verified token UID must be rejected with 403 Forbidden."""
        self.app.dependency_overrides[authentication.get_verified_identity] = lambda: self.mock_identity
        payload = {
            "uid": "forged-different-uid",
            "name": "Impersonator",
            "role": "parent",
            "centerId": "center-001"
        }
        response = self.client.post("/api/auth/profile", json=payload)
        self.app.dependency_overrides.clear()

        self.assertEqual(response.status_code, 403)
        self.assertIn("Profile identity mismatch", response.text)

    def test_offboard_self_forbidden(self):
        """TC-AUTH-08: Admin cannot offboard their own user account (400 Bad Request)."""
        self.app.dependency_overrides[authentication.get_current_user] = lambda: self.mock_user
        response = self.client.post("/api/auth/offboard/admin-01")
        self.app.dependency_overrides.clear()

        self.assertEqual(response.status_code, 400)
        self.assertIn("Cannot offboard yourself", response.text)

    def test_offboard_other_center_user_forbidden(self):
        """TC-AUTH-09: Admin cannot offboard users belonging to another center (403 Forbidden)."""
        self.db.data["users/staff-other-center"] = {
            "uid": "staff-other-center",
            "role": "teacher",
            "status": "approved",
            "centerId": "center-002",
            "email": "other@center2.org"
        }
        self.app.dependency_overrides[authentication.get_current_user] = lambda: self.mock_user
        response = self.client.post("/api/auth/offboard/staff-other-center")
        self.app.dependency_overrides.clear()

        self.assertEqual(response.status_code, 403)
        self.assertIn("User access denied", response.text)

    # ----------------- EDGE CASES -----------------

    def test_register_malformed_center_id_path_traversal(self):
        """TC-AUTH-10: Center ID containing invalid characters or path traversal should fail valid_id check."""
        self.app.dependency_overrides[authentication.get_verified_identity] = lambda: self.mock_identity
        payload = {
            "name": "Attacker",
            "email": "attacker@test.org",
            "password": "Password123!",
            "role": "admin",
            "centerId": "../etc/passwd"
        }
        response = self.client.post("/api/auth/register", json=payload)
        self.app.dependency_overrides.clear()

        self.assertEqual(response.status_code, 400)

    def test_offboard_nonexistent_user(self):
        """TC-AUTH-11: Offboarding a user that does not exist returns 403 or error."""
        self.app.dependency_overrides[authentication.get_current_user] = lambda: self.mock_user
        response = self.client.post("/api/auth/offboard/nonexistent-user-uid")
        self.app.dependency_overrides.clear()

        self.assertEqual(response.status_code, 403)


if __name__ == "__main__":
    unittest.main()
