from django.contrib import admin
from .models import Order, OrderItem
from .models import Purchase


class OrderItemInline(admin.TabularInline):
	model = OrderItem
	extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
	# Show the requested columns in the admin list view
	list_display = ('customer', 'total', 'status', 'created_at')
	list_filter = ('status', 'created_at')
	inlines = [OrderItemInline]


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
	list_display = ('id', 'customer', 'product', 'quantity', 'amount', 'created_at')
	list_filter = ('created_at',)
	search_fields = ('customer__username', 'product__name')