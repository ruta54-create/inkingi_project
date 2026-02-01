from django.shortcuts import render , redirect
from .models import Product 
from django.contrib import messages
from .forms import ProductForm
from accounts.decorators import vendor_required
from django.core.paginator import Paginator 
from django.shortcuts import render, get_object_or_404
from orders.models import OrderItem
from django.db.models import Sum, Q, Count



def home(request):
    products=Product.objects.filter(status='active').order_by('-created_at')[:8]
    return render(request, 'InkingiWoods/home.html', {'products':products})

def product_list(request):
    """
    Task 4.2: Handles product listing, sorting, pagination, and category filtering.
    """
    products = Product.objects.filter(status='active')

    # Search query
    q = request.GET.get('q', '').strip()
    
    # Category filter
    category = request.GET.get('category', '').strip()
    
    sort_by = request.GET.get('sort', '-created_at') 
    
    if sort_by == 'price_asc':
        order_by_field = 'price'
    elif sort_by == 'price_desc':
        order_by_field = '-price'
    else: 
        order_by_field = '-created_at' 
        
    # Apply ordering
    products = products.order_by(order_by_field)

    # Apply search filter if provided
    if q:
        products = products.filter(
            Q(name__icontains=q) | Q(description__icontains=q) | Q(vendor__username__icontains=q)
        )
    
    # Apply category filter if provided
    if category:
        # Map the URL category names to model category values
        category_mapping = {
            'furniture': ['furniture'],
            'home-office': ['home_office'],
            'outdoor-garden': ['outdoor_garden'],
            'doors-construction': ['doors_construction'],
            'handcrafted': ['handcrafted'],
            'custom-made': ['custom_made'],
            'raw-materials': ['raw_materials'],
            'kids-school': ['kids_school'],
        }
        
        if category in category_mapping:
            products = products.filter(category__in=category_mapping[category])

    # Pagination
    paginator = Paginator(products, 12) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'sort_by': sort_by,
        'q': q,
        'category': category,
    }
    
    return render(request, 'products/product_list.html', context)

@vendor_required 
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.vendor = request.user
            product.status = 'active'
            product.save()
            messages.success(request, 'Product added successfully!')
            return redirect('products:vendor_dashboard')
    else:
        form = ProductForm()
    return render(request, 'products/add_product.html', {'form': form})

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk, status='active')
    max_quantity = min(product.stock, 100)
    quantity_range = range(1, max_quantity + 1)

    context = {
        'product': product,
        'quantity_range': quantity_range,
    }
    return render(request, 'products/product_detail.html', context)


@vendor_required
def vendor_dashboard(request):
    vendor = request.user
    total_products = Product.objects.filter(vendor=vendor).count()
    active_products = Product.objects.filter(vendor=vendor, status='active').count()
    out_of_stock = Product.objects.filter(vendor=vendor, stock=0).count()

    # Count order items related to this vendor's products
    pending_order_items = OrderItem.objects.filter(product__vendor=vendor, order__status='pending').count()

    recent_products = Product.objects.filter(vendor=vendor).order_by('-created_at')[:5]

    context = {
        'total_products': total_products,
        'active_products': active_products,
        'out_of_stock': out_of_stock,
        'pending_order_items': pending_order_items,
        'recent_products': recent_products,
    }
    return render(request, 'products/vendor_dashboard.html', context)


@vendor_required
def vendor_products(request):
    vendor = request.user
    products = Product.objects.filter(vendor=vendor).order_by('-created_at')
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'products/vendor_products.html', {'page_obj': page_obj})


@vendor_required
def edit_product(request, pk):
    product = get_object_or_404(Product, pk=pk, vendor=request.user)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product updated successfully.')
            return redirect('products:vendor_products')
    else:
        form = ProductForm(instance=product)
    return render(request, 'products/edit_product.html', {'form': form, 'product': product})


@vendor_required
def delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk, vendor=request.user)
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Product deleted successfully.')
        return redirect('products:vendor_products')
    return render(request, 'products/confirm_delete.html', {'product': product})