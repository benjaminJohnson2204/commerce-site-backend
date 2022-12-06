from django.test import TestCase

from ..models import User


class AuthenticationViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        user = User.objects.create(username="takenUsername", email="takenEmail@gmail.com")
        user.set_password("password")
        user.save()

    def test_valid_register(self):
        response = self.client.post(
            "/api/register",
            {
                "username": "newUsername",
                "email": "newEmail@gmail.com",
                "password": "password",
                "confirmation": "password",
                "receive_emails_order_updates": "False",
                "receive_emails_new_rugs": "True"},
            "application/json"
        )
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, "token")
        token = response.json()["token"]

        authenticated_response = self.client.get("/api/authenticated", HTTP_AUTHORIZATION=f"Token {token}")
        self.assertEqual(authenticated_response.status_code, 200)

        logout_response = self.client.post("/api/logout", HTTP_AUTHORIZATION=f"Token {token}")
        self.assertEqual(logout_response.status_code, 204)

        authenticated_response = self.client.get("/api/authenticated", HTTP_AUTHORIZATION=f"Token {token}")
        self.assertEqual(authenticated_response.status_code, 401)

    def test_register_existing_username(self):
        response = self.client.post(
            "/api/register",
            {"username": "takenUsername", "email": "newEmail@gmail.com", "password": "password", "confirmation": "password"},
            "application/json"
        )
        self.assertEqual(response.status_code, 400)

    def test_register_existing_email(self):
        response = self.client.post(
            "/api/register",
            {"username": "newUsername", "email": "takenEmail@gmail.com", "password": "password", "confirmation": "password"},
            "application/json"
        )
        self.assertEqual(response.status_code, 400)

    def test_register_non_matching_passwords(self):
        response = self.client.post(
            "/api/register",
            {"username": "newUsername", "email": "newEmail@gmail.com", "password": "1", "confirmation": "2"},
            "application/json"
        )
        self.assertEqual(response.status_code, 400)

    def test_register_invalid_email(self):
        response = self.client.post(
            "/api/register",
            {"username": "newUsername", "email": "notAnEmail", "password": "password", "confirmation": "123"},
            "application/json"
        )
        self.assertEqual(response.status_code, 400)

    def test_register_missing_fields(self):
        for data in [
            {"username": "newUsername", "email": "newEmail@gmail.com", "password": "password"},
            {"username": "newUsername", "email": "newEmail@gmail.com", "confirmation": "password"},
            {"username": "newUsername", "password": "password", "confirmation": "password"},
            {"email": "newEmail@gmail.com", "password": "password", "confirmation": "password"},
            {}
        ]:
            response = self.client.post(
                "/api/register",
                data,
                "application/json"
            )
            self.assertEqual(response.status_code, 400)

    def test_valid_login(self):
        response = self.client.post(
            "/api/login",
            {"username": "takenUsername", "password": "password"},
            "application/json"
        )
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, "token")
        token = response.json()["token"]

        authenticated_response = self.client.get("/api/authenticated", HTTP_AUTHORIZATION=f"Token {token}")
        self.assertEqual(authenticated_response.status_code, 200)

        logout_response = self.client.post("/api/logout", HTTP_AUTHORIZATION=f"Token {token}")
        self.assertEqual(logout_response.status_code, 204)

        authenticated_response = self.client.get("/api/authenticated", HTTP_AUTHORIZATION=f"Token {token}")
        self.assertEqual(authenticated_response.status_code, 401)

    def test_login_invalid_username(self):
        response = self.client.post(
            "/api/login",
            {"username": "randomUsername", "password": "password"},
            "application/json"
        )
        self.assertEqual(response.status_code, 400)

        authenticated_response = self.client.get("/api/authenticated")
        self.assertEqual(authenticated_response.status_code, 401)

    def test_login_invalid_password(self):
        response = self.client.post(
            "/api/login",
            {"username": "takenUsername", "password": "randomPassword"},
            "application/json"
        )
        self.assertEqual(response.status_code, 400)

        authenticated_response = self.client.get("/api/authenticated")
        self.assertEqual(authenticated_response.status_code, 401)

    def test_login_missing_fields(self):
        for data in [
            {"username": "takenUsername"},
            {"password": "password"},
            {}
        ]:
            response = self.client.post(
                "/api/login",
                data,
                "application/json"
            )
            self.assertEqual(response.status_code, 400)

            authenticated_response = self.client.get("/api/authenticated")
            self.assertEqual(authenticated_response.status_code, 401)

    def test_verify_password_not_authenticated(self):
        response = self.client.post(
            "/api/verify-password",
            {"password": "password"},
            "application/json"
        )
        self.assertEqual(response.status_code, 401)

    def test_valid_verify_password(self):
        response = self.client.post(
            "/api/login",
            {"username": "takenUsername", "password": "password"},
            "application/json"
        )

        self.assertContains(response, "token")
        token = response.json()["token"]
        response = self.client.post(
            "/api/verify-password",
            {"password": "password"},
            "application/json",
            HTTP_AUTHORIZATION=f"Token {token}"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["password"], "Valid password")

    def test_invalid_verify_password(self):
        response = self.client.post(
            "/api/login",
            {"username": "takenUsername", "password": "password"},
            "application/json"
        )

        self.assertContains(response, "token")
        token = response.json()["token"]

        response = self.client.post(
            "/api/verify-password",
            {"password": "notMyPassword"},
            "application/json",
            HTTP_AUTHORIZATION=f"Token {token}"
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["password"], "Invalid password")
