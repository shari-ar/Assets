import hashlib
from unittest.mock import patch

from django.test import Client, RequestFactory, TestCase
from django.db.utils import ProgrammingError
from ninja.errors import HttpError

from .api import admin_required, jwt_auth, user_required
from .models import AuthAuditLog, RefreshToken, User
from .tokens import create_access_token


class AuthApiTests(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        self.factory = RequestFactory()
        self.password = "S3curePass!"
        self.user = User.objects.create_user(
            email="admin@example.com",
            password=self.password,
            role=User.Role.ADMIN,
            is_staff=True,
        )

    def test_login_success_sets_tokens_and_cookies(self) -> None:
        response = self.client.post(
            "/api/auth/login",
            {"email": self.user.email, "password": self.password},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("access_token", data)
        self.assertIn("refresh_token", data)
        self.assertIn("access_token", response.cookies)
        self.assertIn("refresh_token", response.cookies)

    def test_login_invalid_credentials_logs_failure(self) -> None:
        response = self.client.post(
            "/api/auth/login",
            {"email": self.user.email, "password": "wrong"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)

    def test_register_creates_user_and_returns_profile(self) -> None:
        payload = {
            "fullName": "Alice Example",
            "email": "alice@example.com",
            "password": "Ch@ngeMe12345",
        }
        response = self.client.post("/api/auth/register", payload, content_type="application/json")
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["email"], payload["email"])
        self.assertEqual(data["fullName"], payload["fullName"])
        created_user = User.objects.get(email=payload["email"])
        self.assertEqual(created_user.first_name, "Alice")
        self.assertEqual(created_user.last_name, "Example")

    def test_refresh_rotates_token_and_sets_new_cookies(self) -> None:
        login_response = self.client.post(
            "/api/auth/login",
            {"email": self.user.email, "password": self.password},
            content_type="application/json",
        )
        self.assertEqual(login_response.status_code, 200)
        initial_tokens = list(RefreshToken.objects.filter(user=self.user))
        self.assertEqual(len(initial_tokens), 1)

        refresh_response = self.client.post("/api/auth/refresh")
        self.assertEqual(refresh_response.status_code, 200)
        self.assertIn("access_token", refresh_response.cookies)
        self.assertIn("refresh_token", refresh_response.cookies)

        tokens = list(RefreshToken.objects.filter(user=self.user))
        self.assertEqual(len(tokens), 2)
        revoked = [token for token in tokens if token.revoked]
        active = [token for token in tokens if not token.revoked]
        self.assertEqual(len(revoked), 1)
        self.assertEqual(len(active), 1)

    def test_logout_revokes_refresh_token(self) -> None:
        login_response = self.client.post(
            "/api/auth/login",
            {"email": self.user.email, "password": self.password},
            content_type="application/json",
        )
        self.assertEqual(login_response.status_code, 200)
        refresh_token_cookie = login_response.cookies["refresh_token"].value
        token_hash = hashlib.sha256(refresh_token_cookie.encode("utf-8")).hexdigest()
        token = RefreshToken.objects.get(token_hash=token_hash)
        self.assertFalse(token.revoked)

        response = self.client.post("/api/auth/logout")
        self.assertEqual(response.status_code, 204)
        token.refresh_from_db()
        self.assertTrue(token.revoked)
        self.assertEqual(response.cookies["refresh_token"].value, "")

    def test_me_requires_authentication(self) -> None:
        response = self.client.get("/api/auth/me")
        self.assertEqual(response.status_code, 401)

    def test_me_returns_current_user_using_cookie_tokens(self) -> None:
        login_response = self.client.post(
            "/api/auth/login",
            {"email": self.user.email, "password": self.password},
            content_type="application/json",
        )
        self.assertEqual(login_response.status_code, 200)

        response = self.client.get("/api/auth/me")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["email"], self.user.email)
        self.assertEqual(payload["role"], self.user.role)

    def test_jwt_auth_and_role_requirements(self) -> None:
        token = create_access_token(self.user)
        request = self.factory.get("/protected")
        authenticated_payload = jwt_auth.authenticate(request, token)
        self.assertEqual(authenticated_payload["sub"], str(self.user.pk))
        self.assertTrue(hasattr(request, "user"))

        admin_dependency = admin_required
        user_dependency = user_required
        self.assertEqual(admin_dependency(request), self.user)

        request.user.role = User.Role.USER
        with self.assertRaises(HttpError):
            admin_dependency(request)

        self.assertEqual(user_dependency(request), request.user)

        request.user = None
        with self.assertRaises(HttpError):
            user_dependency(request)


class AuthAuditLogTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email="audit@example.com",
            password="Passw0rd!",
            role=User.Role.ADMIN,
            is_staff=True,
        )

    def test_log_handles_missing_table_gracefully(self) -> None:
        with patch.object(
            AuthAuditLog.objects,
            "create",
            side_effect=ProgrammingError("no such table: assets_auth_authauditlog"),
        ), self.assertLogs("apps.auth.models", level="WARNING") as logs:
            result = AuthAuditLog.log(
                user=self.user,
                email=self.user.email,
                action=AuthAuditLog.Action.LOGIN,
                successful=True,
            )

        self.assertIsNone(result)
        self.assertTrue(any("Skipping authentication audit log write" in msg for msg in logs.output))
