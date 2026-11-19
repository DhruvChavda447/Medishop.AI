from django.contrib import admin
from .models import Cart, Order
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display=['order_ref','user','total','status','created_at']
    list_filter=['status','payment_method']
