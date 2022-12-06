import knox
from django.contrib.auth.views import LogoutView, LoginView
from rest_framework.authtoken.views import obtain_auth_token
from django.urls import path, re_path

from . import views

urlpatterns = [
    # Authentication
    path("register", views.RegisterUserView.as_view(), name="register"),
    path("login", views.LoginUserView.as_view(), name="login"),
    path("logout", knox.views.LogoutView.as_view(), name="logout"),
    path("verify-password", views.VerifyPasswordView.as_view(), name="verify-password"),
    path("authenticated", views.AuthenticatedView.as_view(), name="authenticated"),
    path("user", views.UserView.as_view(), name="user"),
    path("admin", views.AdminView.as_view(), name="admin"),

    # Rugs
    path("rug", views.RugsListView.as_view(), name="all_rugs"),
    path("rug/<int:pk>", views.RugsDetailView.as_view(), name="rug_detail"),

    # Orders
    path("order", views.OrderListView.as_view(), name="all_orders"),
    path("order/<int:pk>", views.OrderDetailView.as_view(), name="order_detail"),

    # Cart
    path("cart", views.CartListView.as_view(), name="cart"),
    path("cart/<int:pk>", views.CartDetailView.as_view(), name="cart_detail"),
    path("cart/size", views.CartSizeView.as_view(), name="cart_size")
]
