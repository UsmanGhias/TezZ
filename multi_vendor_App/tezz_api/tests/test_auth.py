"""Smoke tests for the auth flow.

Run with::

    odoo --test-enable --test-tags tezz_api -i tezz_api -d <db> --stop-after-init
"""
import json

from odoo.tests import HttpCase, tagged


@tagged("tezz_api", "post_install", "-at_install")
class TestAuth(HttpCase):

    def _post(self, path, body):
        return self.url_open(
            f"/api/v1{path}",
            data=json.dumps(body),
            headers={"Content-Type": "application/json"},
        )

    def test_health(self):
        r = self.url_open("/api/v1/health")
        self.assertEqual(r.status_code, 200)
        payload = r.json()
        self.assertEqual(payload["data"]["status"], "ok")
        self.assertIsNone(payload["error"])
        self.assertIn("request_id", payload["meta"])

    def test_signup_login_refresh(self):
        email = "tezz_test_user@example.com"
        # Idempotency: clean up if a previous run left the user behind.
        self.env["res.users"].sudo().search([("login", "=", email)]).unlink()

        r = self._post("/auth/signup", {
            "email": email, "password": "Password123!", "name": "Tezz Tester",
        })
        self.assertEqual(r.status_code, 201, r.text)
        tokens = r.json()["data"]
        self.assertIn("access_token", tokens)
        self.assertIn("refresh_token", tokens)
        self.assertEqual(tokens["user"]["role"], "customer")

        # Login with the same credentials.
        r = self._post("/auth/login",
                       {"email": email, "password": "Password123!"})
        self.assertEqual(r.status_code, 200, r.text)
        login_tokens = r.json()["data"]

        # Refresh.
        r = self._post("/auth/refresh",
                       {"refresh_token": login_tokens["refresh_token"]})
        self.assertEqual(r.status_code, 200, r.text)
        new_tokens = r.json()["data"]
        self.assertNotEqual(new_tokens["refresh_token"], login_tokens["refresh_token"])

        # Old refresh token must be revoked.
        r = self._post("/auth/refresh",
                       {"refresh_token": login_tokens["refresh_token"]})
        self.assertEqual(r.status_code, 401)

    def test_login_bad_password(self):
        r = self._post("/auth/login",
                       {"email": "admin@example.com", "password": "wrong"})
        self.assertEqual(r.status_code, 401)
        self.assertEqual(r.json()["error"]["code"], "unauthorized")

    def test_signup_validation(self):
        r = self._post("/auth/signup", {"email": "nope", "password": "x"})
        self.assertEqual(r.status_code, 422)
        body = r.json()
        self.assertEqual(body["error"]["code"], "validation_error")
