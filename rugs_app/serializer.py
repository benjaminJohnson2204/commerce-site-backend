from django.conf import settings
from django.core.mail import send_mass_mail
from rest_framework import serializers
from .models import User, Rug, Order


class UserSerializer(serializers.ModelSerializer):
    orders = serializers.PrimaryKeyRelatedField(many=True, queryset=Order.objects.all())

    class Meta:
        model = User
        fields = ["username", "email", "password", "orders", "receive_emails_new_rugs"]


class RegisterSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ["username", "email", "password", "receive_emails_order_updates", "receive_emails_new_rugs"]

    def validate(self, attrs):
        # Ensure that username, email, password, and confirmation are provided
        if "username" not in attrs:
            raise serializers.ValidationError({
                "username": "Username not provided"
            })
        if "email" not in attrs:
            raise serializers.ValidationError({
                "email": "Email not provided"
            })
        if "password" not in attrs:
            raise serializers.ValidationError({
                "password": "Password not provided"
            })

        # Ensure that username and email are not already taken
        if len(User.objects.filter(email=attrs["email"])) > 0:
            raise serializers.ValidationError({
                "email": "Email already taken"
            })
        if len(User.objects.filter(username=attrs["username"])) > 0:
            raise serializers.ValidationError({
                "username": "Username already taken"
            })

        return attrs

    def create(self, validated_data):
        user = User.objects.create(
            username=validated_data["username"],
            email=validated_data["email"]
        )

        # Must use set_password method to hash password
        user.set_password(validated_data["password"])

        if "receive_emails_order_updates" in validated_data:
            user.receive_emails_order_updates = validated_data["receive_emails_order_updates"]

        if "receive_emails_new_rugs" in validated_data:
            user.receive_emails_new_rugs = validated_data["receive_emails_new_rugs"]

        user.save()
        return user


class RugSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rug
        fields = "__all__"

    def create(self, validated_data):
        rug = super().create(validated_data)
        email_messages = ((
            "New rug available!",
            f"There is a new rug, \"{validated_data['title']}\", available to purchase! To see this rug, visit "
            f"{settings.CSRF_TRUSTED_ORIGINS[0]}/rug/{rug.id}", settings.DEFAULT_FROM_EMAIL, [user.email])
            for user in User.objects.all() if user.receive_emails_new_rugs)
        send_mass_mail(email_messages, fail_silently=False)
        return rug


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = "__all__"


class VerifyPassword:
    def __init__(self, valid):
        self.valid = valid


class VerifyPasswordSerializer(serializers.Serializer):
    valid = serializers.BooleanField()


class VerifyPasswordRequestSerializer(serializers.Serializer):
    password = serializers.CharField(max_length=128)


class CartPrice:
    def __init__(self, price):
        self.price = price


class CartPriceSerializer(serializers.Serializer):
    price = serializers.DecimalField(max_digits=6, decimal_places=2)