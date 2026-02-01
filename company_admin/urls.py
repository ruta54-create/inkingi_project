from django.urls import path
from . import views

app_name = 'company_admin'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('refund/<int:purchase_id>/', views.refund_purchase, name='refund_purchase'),
]
