from django.shortcuts import render, redirect
from django.contrib import messages
from .models import ContactMessage
from .forms import ContactForm

def about_view(request):
    """About page view"""
    return render(request, 'pages/about.html')

def contact_view(request):
    """Contact page view"""
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # Save to database
            contact_message = form.save()
            # Send email notification (you can add this later)
            messages.success(request, 'Thank you for your message! We will get back to you soon.')
            return redirect('pages:contact')
    else:
        form = ContactForm()
    
    return render(request, 'pages/contact.html', {'form': form})

def privacy_policy_view(request):
    """Privacy Policy page view"""
    return render(request, 'pages/privacy_policy.html')

def terms_of_service_view(request):
    """Terms of Service page view"""
    return render(request, 'pages/terms_of_service.html')

def faq_view(request):
    """FAQ page view"""
    faqs = [
        {
            'question': 'What is Inkingi Wood?',
            'answer': 'Inkingi Wood is a platform for buying and selling quality wood products.'
        },
        {
            'question': 'How do I place an order?',
            'answer': 'Browse products, add to cart, and proceed to checkout.'
        },
        {
            'question': 'What payment methods do you accept?',
            'answer': 'We accept various payment methods including mobile money and bank transfers.'
        },
        {
            'question': 'How long does delivery take?',
            'answer': 'Delivery time depends on your location and product availability, typically 3-7 business days.'
        },
        {
            'question': 'Can I return a product?',
            'answer': 'Yes, we have a 14-day return policy for most products. See our Terms of Service for details.'
        },
    ]
    return render(request, 'pages/faq.html', {'faqs': faqs})