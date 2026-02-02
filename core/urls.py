from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('set-language/', views.set_language, name='set_language'),
    path('set-currency/', views.set_currency, name='set_currency'),
    path('api/exchange-rates/', views.get_exchange_rates, name='exchange_rates'),
    path('api/convert-price/', views.convert_price, name='convert_price'),
]
