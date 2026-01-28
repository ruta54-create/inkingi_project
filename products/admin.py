from django.contrib import admin
from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
	# Show desired columns in admin list view
	list_display = ('name', 'vendor', 'price', 'stock')
	# Keep filters for vendor and status for convenience
	list_filter = ('vendor', 'status')
	search_fields = ('name', 'description')