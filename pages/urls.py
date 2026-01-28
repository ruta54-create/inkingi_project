from django.urls import path
from . import views

app_name = 'pages'

urlpatterns = [
    path('about/', views.about_view, name='about'),
    path('contact/', views.contact_view, name='contact'),
    path('privacy-policy/', views.privacy_policy_view, name='privacy_policy'),
    path('terms-of-service/', views.terms_of_service_view, name='terms_of_service'),
    path('faq/', views.faq_view, name='faq'),
]