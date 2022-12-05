from django.contrib import admin
from .models import User, Rug, Order

# Register your models here.
admin.site.register(User)
admin.site.register(Rug)
admin.site.register(Order)
