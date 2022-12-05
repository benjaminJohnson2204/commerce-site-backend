from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy


class Rug(models.Model):

    class Meta:
        ordering = ["-date_created"]

    class RugStatus(models.TextChoices):
        AVAILABLE = 'av', gettext_lazy('Available'),
        NOT_AVAILABLE = 'na', gettext_lazy('Not available')

    date_created = models.DateTimeField(default=timezone.now, editable=False)
    title = models.CharField(max_length=64)
    description = models.CharField(max_length=1024)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    image_url = models.URLField(max_length=256, blank=True, null=True)
    status = models.CharField(
        max_length=2,
        choices=RugStatus.choices,
        default=RugStatus.AVAILABLE
    )


class User(AbstractUser):
    cart = models.ManyToManyField(Rug, related_name="user")
    receive_emails_order_updates = models.BooleanField(default=True)
    receive_emails_new_rugs = models.BooleanField(default=False)


class Order(models.Model):

    class Meta:
        ordering = ["-date_placed"]

    class OrderStatus(models.TextChoices):
        PENDING = 'pe', gettext_lazy('Pending'),
        READY_FOR_PICKUP = 're', gettext_lazy('Ready for pickup')
        COMPLETE = 'co', gettext_lazy('Complete')

    date_placed = models.DateTimeField(default=timezone.now, editable=False)
    date_ready = models.DateTimeField(null=True)
    date_completed = models.DateTimeField(null=True)

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    rugs = models.ManyToManyField(Rug, related_name="order")
    price = models.DecimalField(max_digits=6, decimal_places=2)
    status = models.CharField(
        max_length=2,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING
    )
