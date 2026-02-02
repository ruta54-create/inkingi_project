# orders/forms.py
from django import forms
import re


class CheckoutForm(forms.Form):
    quantity = forms.IntegerField(
        min_value=1, 
        initial=1, 
        label="Quantity",
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-lg',
            'min': '1',
            'step': '1'
        })
    )
    
    delivery_address = forms.CharField(
        max_length=500, 
        widget=forms.Textarea(attrs={
            'rows': 3,
            'class': 'form-control',
            'placeholder': 'Enter your complete delivery address...'
        }), 
        label="Delivery Address"
    )
    
    phone = forms.CharField(
        max_length=20, 
        label="Phone Number",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+250 788 123 456'
        })
    )
    
    # Enhanced payment choices with descriptions
    PAYMENT_CHOICES = [
        ('bank', 'Bank Transfer'),
        ('momo', 'MTN Mobile Money'),
        ('airtel', 'Airtel Money'),
        ('tigo', 'Tigo Cash'),
        ('card', 'Credit/Debit Card'),
        ('cash', 'Cash on Delivery'),
    ]
    
    payment_method = forms.ChoiceField(
        choices=PAYMENT_CHOICES, 
        initial='momo', 
        widget=forms.RadioSelect(attrs={
            'class': 'payment-method-radio'
        }), 
        label='Payment Method'
    )
    
    mobile_number = forms.CharField(
        max_length=32, 
        required=False, 
        label='Mobile Number',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '0788123456'
        })
    )
    
    # Additional fields for enhanced checkout
    delivery_notes = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 2,
            'class': 'form-control',
            'placeholder': 'Special delivery instructions (optional)...'
        }),
        label="Delivery Notes"
    )
    
    # Delivery options
    DELIVERY_CHOICES = [
        ('standard', 'Standard Delivery (3-5 days) - Free'),
        ('express', 'Express Delivery (1-2 days) - 2,000 RWF'),
        ('pickup', 'Store Pickup - Free'),
    ]
    
    delivery_option = forms.ChoiceField(
        choices=DELIVERY_CHOICES,
        initial='standard',
        widget=forms.RadioSelect(attrs={
            'class': 'delivery-option-radio'
        }),
        label='Delivery Option'
    )

    def clean_mobile_number(self):
        pm = self.cleaned_data.get('payment_method')
        mobile = self.cleaned_data.get('mobile_number', '').strip()
        
        if pm in ('momo', 'airtel', 'tigo'):
            if not mobile:
                raise forms.ValidationError('Mobile number is required for mobile money payments.')
            
            # Enhanced mobile number validation for Rwanda
            if not re.match(r'^(\+?250)?[0-9]{9}$', mobile.replace(' ', '')):
                raise forms.ValidationError('Enter a valid Rwandan mobile number (e.g., 0788123456 or +250788123456).')
        
        return mobile

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        
        # Basic phone validation
        if not re.match(r'^(\+?250)?[0-9]{9}$', phone.replace(' ', '')):
            raise forms.ValidationError('Enter a valid Rwandan phone number.')
        
        return phone

    # GPS coordinates for delivery
    delivery_latitude = forms.DecimalField(
        required=False,
        widget=forms.HiddenInput(attrs={'id': 'delivery_latitude'})
    )

    delivery_longitude = forms.DecimalField(
        required=False,
        widget=forms.HiddenInput(attrs={'id': 'delivery_longitude'})
    )

    def get_delivery_cost(self):
        """Calculate delivery cost based on selected option"""
        delivery_option = self.cleaned_data.get('delivery_option', 'standard')
        delivery_costs = {
            'standard': 0,
            'express': 2000,
            'pickup': 0,
        }
        return delivery_costs.get(delivery_option, 0)


class PaymentProofForm(forms.Form):
    """Form for uploading payment proof"""
    payment_proof = forms.ImageField(
        label='Payment Proof',
        help_text='Upload a screenshot of your payment confirmation (MTN, Airtel, or Bank transfer)',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        })
    )

    payment_reference = forms.CharField(
        max_length=100,
        required=False,
        label='Payment Reference/Transaction ID',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter transaction ID or reference number'
        })
    )


class VendorConfirmationForm(forms.Form):
    """Form for vendor to confirm or reject an order"""
    ACTION_CHOICES = [
        ('confirm', 'Confirm Order'),
        ('reject', 'Reject Order'),
    ]

    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )

    rejection_reason = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Reason for rejection (required if rejecting)'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        rejection_reason = cleaned_data.get('rejection_reason')

        if action == 'reject' and not rejection_reason:
            raise forms.ValidationError('Please provide a reason for rejection.')

        return cleaned_data


class DeliveryTrackingForm(forms.Form):
    """Form for updating delivery tracking"""
    STATUS_CHOICES = [
        ('pending', 'Pending Pickup'),
        ('picked_up', 'Picked Up'),
        ('in_transit', 'In Transit'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('failed', 'Delivery Failed'),
    ]

    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    driver_name = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    driver_phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    vehicle_number = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    current_latitude = forms.DecimalField(
        max_digits=9,
        decimal_places=6,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001'})
    )

    current_longitude = forms.DecimalField(
        max_digits=9,
        decimal_places=6,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001'})
    )

    notes = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2})
    )
