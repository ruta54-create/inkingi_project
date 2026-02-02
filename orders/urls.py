# orders/urls.py
from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    path('checkout/<int:product_id>/', views.checkout, name='checkout'),
    path('payment-processing/<int:order_id>/', views.payment_processing, name='payment_processing'),
    path('payment-confirm/<int:order_id>/', views.payment_confirm, name='payment_confirm'),
    path('confirmation/<int:order_id>/', views.confirmation, name='confirmation'),
    path('my-orders/', views.my_orders, name='my_orders'),
    path('vendor-orders/', views.vendor_orders, name='vendor_orders'),
    path('vendor-orders/<int:order_id>/', views.vendor_order_details, name='vendor_order_details'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart_view, name='cart_view'),
    path('cart/update/', views.update_cart, name='update_cart'),
    path('cart/remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/checkout/', views.checkout_cart, name='checkout_cart'),

    # Payment proof and vendor confirmation
    path('upload-payment-proof/<int:order_id>/', views.upload_payment_proof, name='upload_payment_proof'),
    path('vendor-confirm/<int:order_id>/', views.vendor_confirm_order, name='vendor_confirm_order'),

    # Delivery tracking
    path('track/<int:order_id>/', views.track_delivery, name='track_delivery'),
    path('track/<int:order_id>/update/', views.update_delivery_tracking, name='update_tracking'),
    path('api/tracking/<int:order_id>/', views.get_tracking_location, name='get_tracking_location'),

    path('mock-pay/<int:product_id>/', views.mock_pay, name='mock_pay'),
    path('stripe/checkout/<int:product_id>/', views.stripe_checkout, name='stripe_checkout'),
    path('stripe/webhook/', views.stripe_webhook, name='stripe_webhook'),
    path('stripe/success/<int:order_id>/', views.stripe_success, name='stripe_success'),
    path('stripe/cancel/<int:order_id>/', views.stripe_cancel, name='stripe_cancel'),
    path('stripe/order-status/<int:order_id>/', views.stripe_order_status, name='stripe_order_status'),
    path('site-admin/', views.admin_dashboard, name='site_admin'),
    path('enhanced-admin-dashboard/', views.enhanced_admin_dashboard, name='enhanced_admin_dashboard'),
    path('purchase/<int:pk>/', views.purchase_detail, name='purchase_detail'),
]
