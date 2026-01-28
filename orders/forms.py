# orders/forms.py
from django import forms

class CheckoutForm(forms.Form):
    quantity = forms.IntegerField(min_value=1, initial=1, label="Quantity")
    delivery_address = forms.CharField(max_length=500, widget=forms.Textarea(attrs={'rows':3}), label="Delivery address")
    phone = forms.CharField(max_length=20, label="Phone number")
