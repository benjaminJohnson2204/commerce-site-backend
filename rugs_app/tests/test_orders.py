from django.test import TestCase

from ..models import Rug, User, Order


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
        cls.regular_user1 = User.objects.create_user(username="test1", email="test1@gmail.com", password="test")
        cls.regular_user2 = User.objects.create_user(username="test2", email="test2@gmail.com", password="test")

        cls.orders = [
            Order.objects.create(user=cls.regular_user1, rug_count=1, price=cls.rugs[1].price),
            Order.objects.create(user=cls.regular_user2, rug_count=1, price=cls.rugs[3].price)
        ]
        cls.orders[0].rugs.add(cls.rugs[1])
        cls.orders[1].rugs.add(cls.rugs[3])

    def login_as_user(self, username, password):
        response = self.client.post(
            "/api/login",
            {"username": username, "password": password},
            "application/json"
        )
        return response.json()["token"]

    def test_get_orders_not_authenticated(self):
        orders_response = self.client.get("/api/order")
        self.assertEqual(orders_response.status_code, 401)

    def test_get_orders_authenticated(self):
        token = self.login_as_user(username=self.regular_user1.username, password="test")

        orders_response = self.client.get("/api/order", HTTP_AUTHORIZATION=f"Token {token}")
        self.assertEqual(orders_response.status_code, 200)
        self.assertEqual(orders_response.json()["count"], 1)
        self.assertEqual(orders_response.json()["results"][0]["user"], self.regular_user1.pk)
        self.assertEqual(len(orders_response.json()["results"][0]["rugs"]), 1)
        self.assertEqual(orders_response.json()["results"][0]["rugs"][0], self.rugs[1].pk)
        self.assertEqual(orders_response.json()["results"][0]["status"], Order.OrderStatus.PENDING)

    def test_get_orders_admin(self):
        token = self.login_as_user(username=self.superuser.username, password="admin")

        orders_response = self.client.get("/api/order", HTTP_AUTHORIZATION=f"Token {token}")
        self.assertEqual(orders_response.status_code, 200)
        self.assertEqual(orders_response.json()["count"], 2)

        results = orders_response.json()["results"]
        order_1 = results[0] if results[0]["user"] == self.regular_user1.pk else results[1]
        order_2 = results[0] if results[0]["user"] == self.regular_user2.pk else results[1]

        self.assertEqual(len(order_2["rugs"]), 1)
        self.assertEqual(order_2["rugs"][0], self.rugs[3].pk)
        self.assertEqual(order_2["status"], Order.OrderStatus.PENDING)

        self.assertEqual(len(order_1["rugs"]), 1)
        self.assertEqual(order_1["rugs"][0], self.rugs[1].pk)
        self.assertEqual(order_1["status"], Order.OrderStatus.PENDING)

    def test_place_order_not_authenticated(self):
        add_to_cart_response = self.client.post(
            "/api/cart",
            {"rug": self.rugs[0].pk},
            "application/json"
        )
        self.assertEqual(add_to_cart_response.status_code, 401)

        place_order_response = self.client.post("/api/order")
        self.assertEqual(place_order_response.status_code, 401)

    def test_place_order_authenticated(self):
        token = self.login_as_user(username=self.regular_user1.username, password="test")

        add_to_cart_response = self.client.post(
            "/api/cart",
            {"rug": self.rugs[0].pk},
            "application/json",
            HTTP_AUTHORIZATION=f"Token {token}"
        )
        self.assertEqual(add_to_cart_response.status_code, 201)

        existing_rug_in_cart_response = self.client.get(f"/api/cart/{self.rugs[0].pk}", HTTP_AUTHORIZATION=f"Token {token}")
        self.assertEqual(existing_rug_in_cart_response.status_code, 200)
        self.assertEqual(existing_rug_in_cart_response.json()["id"], self.rugs[0].pk)

        nonexistent_rug_in_cart_response = self.client.get(f"/api/cart/{self.rugs[1].pk}", HTTP_AUTHORIZATION=f"Token {token}")
        self.assertEqual(nonexistent_rug_in_cart_response.status_code, 404)

        place_order_response = self.client.post("/api/order", HTTP_AUTHORIZATION=f"Token {token}")
        self.assertEqual(place_order_response.status_code, 201)

        cart_response = self.client.get("/api/cart", HTTP_AUTHORIZATION=f"Token {token}")
        self.assertEqual(cart_response.status_code, 200)

        self.assertEqual(len(cart_response.json()["results"]), 0)

        cart_price_response = self.client.get("/api/cart/price", HTTP_AUTHORIZATION=f"Token {token}")
        self.assertEqual(float(cart_price_response.json()["price"]), 0)

        orders_response = self.client.get("/api/order", HTTP_AUTHORIZATION=f"Token {token}")
        self.assertEqual(orders_response.status_code, 200)
        self.assertEqual(orders_response.json()["count"], 2)
        self.assertEqual(len(orders_response.json()["results"][1]["rugs"]), 1)
        self.assertEqual(orders_response.json()["results"][1]["rug_count"], 1)

        ordered_rug = Rug.objects.get(pk=orders_response.json()["results"][1]["rugs"][0])
        self.assertEqual(ordered_rug.status, Rug.RugStatus.NOT_AVAILABLE)

    def test_get_cart(self):
        token = self.login_as_user(username=self.regular_user1.username, password="test")

        add_to_cart_response = self.client.post(
            "/api/cart",
            {"rug": self.rugs[0].pk},
            "application/json",
            HTTP_AUTHORIZATION=f"Token {token}"
        )
        self.assertEqual(add_to_cart_response.status_code, 201)

        cart_response = self.client.get("/api/cart", HTTP_AUTHORIZATION=f"Token {token}")

        self.assertEqual(cart_response.status_code, 200)
        self.assertEqual(len(cart_response.json()["results"]), 1)

        cart_price_response = self.client.get("/api/cart/price", HTTP_AUTHORIZATION=f"Token {token}")
        self.assertEqual(float(cart_price_response.json()["price"]), self.rugs[0].price)

    def test_delete_from_cart(self):
        token = self.login_as_user(username=self.regular_user1.username, password="test")

        self.client.post(
            "/api/cart",
            {"rug": self.rugs[0].pk},
            "application/json",
            HTTP_AUTHORIZATION=f"Token {token}"
        )
        self.client.post(
            "/api/cart",
            {"rug": self.rugs[2].pk},
            "application/json",
            HTTP_AUTHORIZATION=f"Token {token}"
        )

        delete_from_cart_response = self.client.delete(f"/api/cart/{self.rugs[0].pk}", HTTP_AUTHORIZATION=f"Token {token}")
        self.assertEqual(delete_from_cart_response.status_code, 204)

        cart_response = self.client.get("/api/cart", HTTP_AUTHORIZATION=f"Token {token}")
        self.assertEqual(cart_response.status_code, 200)

        self.assertEqual(len(cart_response.json()["results"]), 1)

        cart_price_response = self.client.get("/api/cart/price", HTTP_AUTHORIZATION=f"Token {token}")
        self.assertEqual(float(cart_price_response.json()["price"]), self.rugs[2].price)

    def test_delete_entire_cart(self):
        token = self.login_as_user(username=self.regular_user1.username, password="test")

        self.client.post(
            "/api/cart",
            {"rug": self.rugs[0].pk},
            "application/json",
            HTTP_AUTHORIZATION=f"Token {token}"
        )
        self.client.post(
            "/api/cart",
            {"rug": self.rugs[2].pk},
            "application/json",
            HTTP_AUTHORIZATION=f"Token {token}"
        )

        delete_response = self.client.delete("/api/cart", HTTP_AUTHORIZATION=f"Token {token}")
        self.assertEqual(delete_response.status_code, 204)

        cart_response = self.client.get("/api/cart", HTTP_AUTHORIZATION=f"Token {token}")
        self.assertEqual(cart_response.status_code, 200)

        self.assertEqual(len(cart_response.json()["results"]), 0)

        cart_price_response = self.client.get("/api/cart/price", HTTP_AUTHORIZATION=f"Token {token}")
        self.assertEqual(float(cart_price_response.json()["price"]), 0)

    def test_place_order_no_rugs(self):
        token = self.login_as_user(username=self.regular_user1.username, password="test")

        place_order_response = self.client.post(
            "/api/order",
            HTTP_AUTHORIZATION=f"Token {token}"
        )
        self.assertEqual(place_order_response.status_code, 400)

        orders_response = self.client.get("/api/order", HTTP_AUTHORIZATION=f"Token {token}")
        self.assertEqual(orders_response.status_code, 200)
        self.assertEqual(orders_response.json()["count"], 1)

    def test_get_order_by_id_not_authenticated(self):
        orders_response = self.client.get(f"/api/order/{self.orders[0].pk}")
        self.assertEqual(orders_response.status_code, 401)

    def test_get_order_by_id_wrong_user(self):
        token = self.login_as_user(username=self.regular_user2.username, password="test")

        orders_response = self.client.get(f"/api/order/{self.orders[0].pk}", HTTP_AUTHORIZATION=f"Token {token}")
        self.assertEqual(orders_response.status_code, 403)

    def test_get_order_by_id_correct_user(self):
        token = self.login_as_user(username=self.regular_user1.username, password="test")

        orders_response = self.client.get(f"/api/order/{self.orders[0].pk}", HTTP_AUTHORIZATION=f"Token {token}")
        self.assertEqual(orders_response.status_code, 200)

        self.assertEqual(orders_response.json()["user"], self.regular_user1.pk)
        self.assertEqual(orders_response.json()["rug_count"], 1)
        self.assertEqual(orders_response.json()["status"], Order.OrderStatus.PENDING)

    def test_get_rugs_by_order_wrong_user(self):
        token = self.login_as_user(username=self.regular_user2.username, password="test")

        rugs_response = self.client.get(f"/api/rug/by-order/{self.orders[0].pk}", HTTP_AUTHORIZATION=f"Token {token}")
        self.assertEqual(rugs_response.status_code, 403)

    def test_get_rugs_by_order_correct_user(self):
        token = self.login_as_user(username=self.regular_user1.username, password="test")
        rugs_response = self.client.get(f"/api/rug/by-order/{self.orders[0].pk}", HTTP_AUTHORIZATION=f"Token {token}")
        self.assertEqual(rugs_response.json()["results"][0]["id"], self.orders[0].rugs.first().pk)

    def test_get_order_by_id_admin(self):
        token = self.login_as_user(username=self.superuser.username, password="admin")

        orders_response = self.client.get(f"/api/order/{self.orders[0].pk}", HTTP_AUTHORIZATION=f"Token {token}")
        self.assertEqual(orders_response.status_code, 200)

    def test_modify_order_not_authenticated(self):
        modify_order_response = self.client.patch(
            f"/api/order/{self.orders[0].pk}",
            {"status": Order.OrderStatus.COMPLETE},
            "application/json"
        )
        self.assertEqual(modify_order_response.status_code, 401)

    def test_modify_order_wrong_user(self):
        token = self.login_as_user(username=self.regular_user2.username, password="test")
        modify_order_response = self.client.patch(
            f"/api/order/{self.orders[0].pk}",
            {"status": Order.OrderStatus.COMPLETE},
            "application/json",
            HTTP_AUTHORIZATION=f"Token {token}"
        )
        self.assertEqual(modify_order_response.status_code, 403)

    def test_modify_order_correct_user(self):
        token = self.login_as_user(username=self.regular_user1.username, password="test")
        modify_order_response = self.client.patch(
            f"/api/order/{self.orders[0].pk}",
            {"status": Order.OrderStatus.COMPLETE},
            "application/json",
            HTTP_AUTHORIZATION=f"Token {token}"
        )
        self.assertEqual(modify_order_response.status_code, 200)

        orders_response = self.client.get(f"/api/order/{self.orders[0].pk}", HTTP_AUTHORIZATION=f"Token {token}")
        self.assertEqual(orders_response.status_code, 200)

        self.assertEqual(orders_response.json()["status"], Order.OrderStatus.COMPLETE)
        self.assertIsNotNone(orders_response.json()["date_completed"])

    def test_modify_order_admin(self):
        token = self.login_as_user(username=self.superuser.username, password="admin")
        modify_order_response = self.client.patch(
            f"/api/order/{self.orders[0].pk}",
            {"status": Order.OrderStatus.READY_FOR_PICKUP},
            "application/json",
            HTTP_AUTHORIZATION=f"Token {token}"
        )
        self.assertEqual(modify_order_response.status_code, 200)

        orders_response = self.client.get(f"/api/order/{self.orders[0].pk}", HTTP_AUTHORIZATION=f"Token {token}")
        self.assertEqual(orders_response.status_code, 200)

        self.assertEqual(orders_response.json()["status"], Order.OrderStatus.READY_FOR_PICKUP)
        self.assertIsNotNone(orders_response.json()["date_ready"])

    def test_delete_order_not_authenticated(self):
        delete_order_response = self.client.delete(f"/api/order/{self.orders[0].pk}")
        self.assertEqual(delete_order_response.status_code, 401)

    def test_delete_order_wrong_user(self):
        token = self.login_as_user(username=self.regular_user2.username, password="test")
        delete_order_response = self.client.delete(f"/api/order/{self.orders[0].pk}", HTTP_AUTHORIZATION=f"Token {token}")
        self.assertEqual(delete_order_response.status_code, 403)

    def test_delete_order_correct_user(self):
        token = self.login_as_user(username=self.regular_user1.username, password="test")

        delete_order_response = self.client.delete(f"/api/order/{self.orders[0].pk}", HTTP_AUTHORIZATION=f"Token {token}")
        self.assertEqual(delete_order_response.status_code, 204)

        orders_response = self.client.get(f"/api/order/{self.orders[0].pk}", HTTP_AUTHORIZATION=f"Token {token}")
        self.assertEqual(orders_response.status_code, 404)

    def test_delete_order_admin(self):
        token = self.login_as_user(username=self.superuser.username, password="admin")

        delete_order_response = self.client.delete(f"/api/order/{self.orders[0].pk}", HTTP_AUTHORIZATION=f"Token {token}")
        self.assertEqual(delete_order_response.status_code, 204)

        orders_response = self.client.get(f"/api/order/{self.orders[0].pk}", HTTP_AUTHORIZATION=f"Token {token}")
        self.assertEqual(orders_response.status_code, 404)
