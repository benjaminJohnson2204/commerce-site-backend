import django
import knox.views
from django.contrib.auth import login, authenticate
from django.contrib.auth.views import LoginView
from django.core.mail import send_mass_mail
from django.forms import forms
from django.http import JsonResponse, HttpResponseRedirect
from django.middleware.csrf import get_token
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiResponse, OpenApiParameter
from knox.models import AuthToken
from rest_framework import generics, serializers
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.generics import GenericAPIView
from rest_framework.parsers import JSONParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.permissions import AllowAny, IsAuthenticated, BasePermission, SAFE_METHODS, IsAdminUser, \
    DjangoObjectPermissions
from .models import User, Order, Rug

from .serializer import RegisterSerializer, UserSerializer, RugSerializer, OrderSerializer, VerifyPasswordSerializer, \
    CartSizeSerializer, VerifyPassword, CartSize, VerifyPasswordRequestSerializer
from django.conf import settings


class IsAdminOrOwnsOrder(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user.is_staff or request.user == obj.user


class ReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS


@extend_schema_view(
    post=extend_schema(
        tags=["Register"],
        description="Registers a new user and returns their token",
        responses=AuthTokenSerializer
    )
)
class RegisterUserView(generics.CreateAPIView):
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        # Ensure that passwords match
        if request.data.get("password") != request.data.get("confirmation"):
            raise serializers.ValidationError({
                "password": "Passwords don't match"
            })
        super().create(request, *args, **kwargs)
        user = authenticate(request, username=request.data.get("username"), password=request.data.get("password"))
        if user is not None:
            token = AuthToken.objects.create(user)
            return Response({
                "token": token[1]
            })
        raise serializers.ValidationError({
            "error": "cannot register"
        })


class LoginUserView(APIView):
    permission_classes = (AllowAny,)
    serializer_class = UserSerializer

    @extend_schema(
        tags=["Login"],
        description="Logs a user in and returns their token",
        responses=AuthTokenSerializer
    )
    def post(self, request):
        user = authenticate(request, **request.data)
        if user is not None:
            token = AuthToken.objects.create(user)
            return Response({
                "token": token[1]
            })
        raise serializers.ValidationError({
            "error": "cannot login"
        })


@extend_schema(
    tags=["Logout"],
    description="Logs a user out"
)
class LogoutUserView(knox.views.LogoutView):
    serializer_class = None


class VerifyPasswordView(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = VerifyPasswordRequestSerializer

    @extend_schema(
        tags=["Verify Password"],
        description="Takes a user's inputted password and verifies that it is truly their password",
        responses=VerifyPasswordSerializer
    )
    def post(self, request):
        user = authenticate(request, username=request.user.username, password=request.data.get("password"))
        if user is not None:
            verify_password = VerifyPasswordSerializer(VerifyPassword(valid=True))
            return Response(verify_password.data)
        raise serializers.ValidationError({
            "valid": False
        })


class AuthenticatedView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer

    @extend_schema(
        tags=["Authenticated"],
        description="Returns the user if they are authenticated",
        request=None
    )
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class AdminView(GenericAPIView):
    permission_classes = (IsAdminUser,)
    serializer_class = UserSerializer

    @extend_schema(
        tags=["Admin"],
        description="Returns the user if they are an admin user",
        request=None
    )
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class UserView(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer

    @extend_schema(
        tags=["User"],
        description="Updates a user's email preferences"
    )
    def patch(self, request, *args, **kwargs):
        try:
            request.user.receive_emails_new_rugs = request.data["receive_emails_new_rugs"]
            request.user.save()
            return Response("Successfully updated email preferences")
        except Exception:
            return JsonResponse({"error": "Could not update email preferences"}, status=400)


@extend_schema(
    tags=["Rugs"]
)
class RugsListView(generics.ListCreateAPIView):
    permission_classes = (IsAdminUser | ReadOnly,)
    queryset = Rug.objects.all()
    serializer_class = RugSerializer
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filterset_fields = ["status"]
    search_fields = ["title", "description"]  # <url>?search=<search>
    ordering_fields = ["title", "price"]  # <url>?ordering=title, use ordering=-title for descending

    @extend_schema(
        description="Gets all available rugs, with options for "
                    "searching, filtering, and sorting",
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        description="Create a new rug (must be admin)"
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


@extend_schema(
    tags=["Rugs"]
)
class RugsDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAdminUser | ReadOnly,)
    queryset = Rug.objects.all()
    serializer_class = RugSerializer

    @extend_schema(
        description="Gets a certain rug by its ID"
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        description="Update a rug (must be admin)"
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    @extend_schema(
        description="Delete a rug (must be admin)"
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


@extend_schema(
    tags=["Orders"],
)
class OrderListView(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def get_queryset(self):
        if self.request.user.is_staff:
            return super().get_queryset()
        return self.queryset.filter(user=self.request.user)

    @extend_schema(
        description="Gets all a user's orders, or all existing orders for an admin user"
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        tags=["Orders"],
        description="Create an order of all rugs in the user's cart, and clears the cart"
    )
    def post(self, request, *args, **kwargs):
        for rug in request.user.cart.all():
            if not rug:
                print("non existent rug")
                raise serializers.ValidationError({
                    "error": "one or more rugs in order does not exist"
                })
            if rug.status != Rug.RugStatus.AVAILABLE:
                print("non available rug")
                raise serializers.ValidationError({
                    "error": "one or more rugs in order is not available"
                })

        # Manually serialize in order to include user
        serializer = OrderSerializer(data={
            "user": request.user.pk,
            "rugs": [rug.pk for rug in request.user.cart.all()],
            "price": sum(rug.price for rug in request.user.cart.all())
        })
        if serializer.is_valid():
            # Order is validated, set rugs to no longer be available
            for rug in request.user.cart.all():
                rug.status = Rug.RugStatus.NOT_AVAILABLE
                rug.save()
            request.user.cart.clear()
            request.user.save()

            serializer.save()
            return JsonResponse(serializer.data, status=201)
        return JsonResponse(serializer.errors, status=400)


@extend_schema(
    tags=["Orders"],
)
class OrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAdminOrOwnsOrder,)
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    @extend_schema(
        description="Gets an order by its ID; only allowed if it is the user's order or the user is an admin"
    )
    def get(self, request, pk):
        try:
            order = Order.objects.get(pk=pk)
        except Order.DoesNotExist:
            return JsonResponse({}, status=404)

        if order.user != request.user and not request.user.is_staff:
            return JsonResponse({}, status=403)

        order_serializer = OrderSerializer(order)
        rugs_serializer = RugSerializer(Rug.objects.filter(id__in=order_serializer.data["rugs"]), many=True)
        return JsonResponse({
            "order": order_serializer.data,
            "rugs": rugs_serializer.data
        })

    @extend_schema(
        description="Updates an order by its ID; only allowed if it is the user's order or the user is an admin"
    )
    @action(detail=True, methods=["put"])
    def partial_update(self, request, *args, **kwargs):
        if "status" in request.data:
            status = request.data.get("status")
            order = Order.objects.get(pk=kwargs["pk"])
            if status == Order.OrderStatus.READY_FOR_PICKUP:
                order.date_ready = timezone.now()
            elif status == Order.OrderStatus.COMPLETE:
                order.date_completed = timezone.now()
            order.save()
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        description="Deletes an order by its ID; only allowed if it is the user's order or the user is an admin"
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


@extend_schema(
    tags=["Cart"]
)
class CartListView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = Rug.objects.all()
    serializer_class = RugSerializer

    def get_queryset(self):
        return self.request.user.cart.all()

    @extend_schema(
        description="Gets all rugs in a user's cart, along with the total price of the rugs"
    )
    def get(self, request, *args, **kwargs):
        serializer = RugSerializer(self.get_queryset(), many=True)
        return JsonResponse({
            "cart": serializer.data,
            "price": sum(rug.price for rug in request.user.cart.all())
        })

    @extend_schema(
        description="Add a rug to the user's cart"
    )
    def post(self, request):
        rug = Rug.objects.get(pk=request.data.get("rug"))
        if not rug:
            raise serializers.ValidationError({
                "error": "rug does not exist"
            })
        if rug.status != Rug.RugStatus.AVAILABLE:
            raise serializers.ValidationError({
                "error": "rug is not available"
            })
        request.user.cart.add(rug.pk)
        request.user.save()
        return JsonResponse("Successfully added to cart", status=201, safe=False)

    @extend_schema(
        operation_id="api_cart_destroy_all",
        description="Deletes all rugs from the user's cart"
    )
    def delete(self, request):
        request.user.cart.clear()
        request.user.save()
        return JsonResponse({}, status=204)


@extend_schema(
    tags=["Cart"]
)
class CartDetailView(generics.RetrieveAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = RugSerializer

    def get_queryset(self):
        return self.request.user.cart.all()

    @extend_schema(
        description="Gets a rug from the user's cart by ID"
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        operation_id="api_cart_destroy_one",
        description="Deletes a rug from the user's cart by ID"
    )
    def delete(self, request, pk):
        rug = Rug.objects.get(pk=pk)
        if not rug:
            raise serializers.ValidationError({
                "error": "rug does not exist"
            })
        request.user.cart.remove(Rug.objects.get(pk=pk))
        request.user.save()
        return JsonResponse({}, status=204)


class CartSizeView(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = CartSizeSerializer

    @extend_schema(
        tags=["Cart Size"],
        description="Gets the number of rugs currently in the user's cart"
    )
    def get(self, request):
        cart_size = CartSizeSerializer(CartSize(
            size=request.user.cart.count()
        ))
        return Response(cart_size.data)
