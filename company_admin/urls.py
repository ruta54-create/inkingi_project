from django.urls import path
from . import views

app_name = 'company_admin'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),

    # Vendor management
    path('vendors/', views.vendor_management, name='vendor_management'),
    path('vendors/<int:vendor_id>/', views.vendor_detail, name='vendor_detail'),

    # Order management
    path('orders/', views.order_management, name='order_management'),
    path('orders/<int:order_id>/', views.order_detail_admin, name='order_detail'),
    path('orders/<int:order_id>/update-status/', views.update_order_status, name='update_order_status'),

    # Delivery management
    path('deliveries/', views.delivery_management, name='delivery_management'),

    # User management
    path('users/', views.user_management, name='user_management'),

    # Site settings
    path('settings/', views.site_settings, name='site_settings'),

    # Currency management
    path('currencies/', views.currency_management, name='currency_management'),

    # Refunds
    path('refund/<int:purchase_id>/', views.refund_purchase, name='refund_purchase'),
]
