from django.contrib import admin

from .models import Sneaker, Order, OrderItem


@admin.register(Sneaker)
class SneakerAdmin(admin.ModelAdmin):
    list_display = ("name", "price")


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "customer_name", "phone", "created_at")
    inlines = [OrderItemInline]

