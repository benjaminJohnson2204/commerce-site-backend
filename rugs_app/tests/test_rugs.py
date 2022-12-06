from datetime import datetime

from django.test import TestCase
from rest_framework.parsers import JSONParser

from ..models import Rug, User


class RugsViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.rugs = [
            Rug.objects.create(title="Test1", description="Testing1", price=4.99),
            Rug.objects.create(title="Test2", description="Testing2", price=5.99, image_url="some_image.com", status=Rug.RugStatus.NOT_AVAILABLE),
            Rug.objects.create(title="Test3", description="Testing3", price=7.99, image_url="another_image.com"),
            Rug.objects.create(title="Test4", description="Testing4", price=9.99, status=Rug.RugStatus.NOT_AVAILABLE),
        ]

        cls.superuser = User.objects.create_superuser(username="admin", email="admin@gmail.com", password="admin")
        cls.regular_user = User.objects.create_user(username="test", email="test@gmail.com", password="test")

    def login_as_user(self, username, password):
        response = self.client.post(
            "/api/login",
            {"username": username, "password": password},
            "application/json"
        )
        return response.json()["token"]
    
    def test_get_all_rugs(self):
        all_rugs_response = self.client.get("/api/rug")
        self.assertEqual(all_rugs_response.status_code, 200)
        self.assertEqual(all_rugs_response.json()["count"], 4)

    def test_create_rug_not_authenticated(self):
        create_rug_response = self.client.post(
            "/api/rug",
            {"title": "Test5", "description": "Testing5", "price": "3.99"},
            "application/json"
        )
        self.assertEqual(create_rug_response.status_code, 401)

        all_rugs_response = self.client.get("/api/rug")
        self.assertEqual(all_rugs_response.status_code, 200)
        self.assertEqual(all_rugs_response.json()["count"], 4)

    def test_create_rug_regular_user(self):
        token = self.login_as_user(username=self.regular_user.username, password="test")

        create_rug_response = self.client.post(
            "/api/rug",
            {"title": "Test5", "description": "Testing5", "price": "3.99"},
            "application/json",
            HTTP_AUTHORIZATION=f"Token {token}"
        )
        self.assertEqual(create_rug_response.status_code, 403)

        all_rugs_response = self.client.get("/api/rug")
        self.assertEqual(all_rugs_response.status_code, 200)
        self.assertEqual(all_rugs_response.json()["count"], 4)

    def test_create_rug_admin(self):
        token = self.login_as_user(username=self.superuser.username, password="admin")

        create_rug_response = self.client.post(
            "/api/rug",
            {"title": "Test5", "description": "Testing5", "price": "3.99"},
            "application/json",
            HTTP_AUTHORIZATION=f"Token {token}"
        )
        self.assertEqual(create_rug_response.status_code, 201)

        all_rugs_response = self.client.get("/api/rug", HTTP_AUTHORIZATION=f"Token {token}")
        self.assertEqual(all_rugs_response.status_code, 200)
        self.assertEqual(all_rugs_response.json()["count"], 5)

    def test_get_rug_by_id(self):
        for rug in self.rugs:
            get_rug_response = self.client.get(f"/api/rug/{rug.pk}")
            self.assertEqual(get_rug_response.status_code, 200)
            self.assertEqual(get_rug_response.json()["title"], rug.title)
            self.assertEqual(get_rug_response.json()["description"], rug.description)
            self.assertEqual(float(get_rug_response.json()["price"]), rug.price)
            self.assertEqual(get_rug_response.json()["image_url"], rug.image_url)
            self.assertEqual(get_rug_response.json()["status"], rug.status)
            self.assertIsNotNone(get_rug_response.json()["date_created"])

    def test_modify_rug_not_authenticated(self):
        modify_rug_response = self.client.patch(
            f"/api/rug/{self.rugs[0].pk}",
            {"title": "NewTitle"},
            "application/json"
        )
        self.assertEqual(modify_rug_response.status_code, 401)

        rug_response = self.client.get(f"/api/rug/{self.rugs[0].pk}")
        self.assertEqual(rug_response.status_code, 200)
        self.assertEqual(rug_response.json()["title"], "Test1")

    def test_modify_rug_regular_user(self):
        token = self.login_as_user(username=self.regular_user.username, password="test")

        modify_rug_response = self.client.patch(
            f"/api/rug/{self.rugs[0].pk}",
            {"title": "NewTitle"},
            "application/json",
            HTTP_AUTHORIZATION=f"Token {token}"
        )
        self.assertEqual(modify_rug_response.status_code, 403)

        rug_response = self.client.get(f"/api/rug/{self.rugs[0].pk}")
        self.assertEqual(rug_response.status_code, 200)
        self.assertEqual(rug_response.json()["title"], "Test1")

    def test_modify_rug_admin(self):
        token = self.login_as_user(username=self.superuser.username, password="admin")

        modify_rug_response = self.client.patch(
            f"/api/rug/{self.rugs[0].pk}",
            {"title": "NewTitle"},
            "application/json",
            HTTP_AUTHORIZATION=f"Token {token}"
        )
        self.assertEqual(modify_rug_response.status_code, 200)

        rug_response = self.client.get(f"/api/rug/{self.rugs[0].pk}", HTTP_AUTHORIZATION=f"Token {token}")
        self.assertEqual(rug_response.status_code, 200)
        self.assertEqual(rug_response.json()["title"], "NewTitle")

    def test_delete_rug_not_authenticated(self):
        delete_rug_response = self.client.delete(
            f"/api/rug/{self.rugs[0].pk}"
        )
        self.assertEqual(delete_rug_response.status_code, 401)

        rug_response = self.client.get(f"/api/rug/{self.rugs[0].pk}")
        self.assertEqual(rug_response.status_code, 200)
        self.assertIsNotNone(rug_response.json())

    def test_delete_rug_regular_user(self):
        token = self.login_as_user(username=self.regular_user.username, password="test")

        delete_rug_response = self.client.delete(
            f"/api/rug/{self.rugs[0].pk}",
            HTTP_AUTHORIZATION=f"Token {token}"
        )
        self.assertEqual(delete_rug_response.status_code, 403)

        rug_response = self.client.get(f"/api/rug/{self.rugs[0].pk}", HTTP_AUTHORIZATION=f"Token {token}")
        self.assertEqual(rug_response.status_code, 200)
        self.assertIsNotNone(rug_response.json())

    def test_delete_rug_admin(self):
        token = self.login_as_user(username=self.superuser.username, password="admin")

        delete_rug_response = self.client.delete(
            f"/api/rug/{self.rugs[0].pk}",
            HTTP_AUTHORIZATION=f"Token {token}"
        )
        self.assertEqual(delete_rug_response.status_code, 204)

        rug_response = self.client.get(f"/api/rug/{self.rugs[0].pk}", HTTP_AUTHORIZATION=f"Token {token}")
        self.assertEqual(rug_response.status_code, 404)

        all_rugs_response = self.client.get("/api/rug", HTTP_AUTHORIZATION=f"Token {token}")
        self.assertEqual(all_rugs_response.status_code, 200)
        self.assertEqual(all_rugs_response.json()["count"], 3)
