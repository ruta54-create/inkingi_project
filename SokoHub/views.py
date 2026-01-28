from django.shortcuts import render
from products.models import Product


def home(request):
    try:
        newest_products = Product.objects.filter(status='active').order_by('-created_at')[:8]
    except Exception as e:
        print(f"Error fetching newest products: {e}")
        newest_products = []

    # Provide `products` in context so `templates/InkingiWoods/home.html` can iterate over them
    context = {'products': newest_products}
    return render(request, 'InkingiWoods/home.html', context)
