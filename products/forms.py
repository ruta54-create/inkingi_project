from django import forms
from .models import Product

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'stock', 'unit', 'category', 'image']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control form-control-lg', 
                'placeholder': 'Enter product name (e.g., Modern Wooden Chair)'
            }),
            'description': forms.Textarea(attrs={
                'rows': 4, 
                'class': 'form-control', 
                'placeholder': 'Describe your product features, materials, dimensions, and benefits...'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg', 
                'placeholder': '0.00', 
                'step': '0.01',
                'min': '0.01'
            }),
            'stock': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg', 
                'placeholder': 'Available quantity',
                'min': '0'
            }),
            'unit': forms.TextInput(attrs={
                'class': 'form-control form-control-lg', 
                'placeholder': 'e.g., pcs, meter, sqm, kg, bundle',
                'list': 'unit-suggestions',
                'autocomplete': 'off'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select form-select-lg'
            }),
            'image': forms.ClearableFileInput(attrs={
                'class': 'form-control form-control-lg',
                'accept': 'image/*'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add helpful labels and help text
        self.fields['name'].label = 'Product Name'
        self.fields['name'].help_text = 'Choose a clear, descriptive name that customers will search for'
        
        self.fields['description'].label = 'Product Description'
        self.fields['description'].help_text = 'Provide detailed information about materials, dimensions, features, and benefits'
        
        self.fields['price'].label = 'Price (RWF)'
        self.fields['price'].help_text = 'Set a competitive price in Rwandan Francs'
        
        self.fields['stock'].label = 'Stock Quantity'
        self.fields['stock'].help_text = 'How many units do you have available?'
        
        self.fields['unit'].label = 'Unit of Measurement'
        self.fields['unit'].help_text = 'Specify how your product is sold (pieces, meters, kilograms, etc.)'
        
        self.fields['category'].label = 'Product Category'
        self.fields['category'].help_text = 'Choose the category that best describes your product'
        
        self.fields['image'].label = 'Product Image'
        self.fields['image'].help_text = 'Upload a high-quality image (JPG, PNG, max 5MB)'

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price <= 0:
            raise forms.ValidationError("Price must be positive.")
        if price > 10000000:  # 10 million RWF limit
            raise forms.ValidationError("Price seems too high. Please check your input.")
        return price

    def clean_stock(self):
        stock = self.cleaned_data.get('stock')
        if stock < 0:
            raise forms.ValidationError("Stock cannot be negative.")
        if stock > 100000:  # Reasonable stock limit
            raise forms.ValidationError("Stock quantity seems too high. Please check your input.")
        return stock

    def clean_unit(self):
        unit = self.cleaned_data.get('unit', '').strip().lower()
        if not unit:
            raise forms.ValidationError("Unit is required.")
        
        # Remove any special characters and normalize
        import re
        unit = re.sub(r'[^\w\s\²\³]', '', unit)
        unit = unit.replace(' ', '_')
        
        # Limit length
        if len(unit) > 50:
            raise forms.ValidationError("Unit name is too long (max 50 characters).")
            
        return unit

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if len(name) < 3:
            raise forms.ValidationError("Product name must be at least 3 characters long.")
        if len(name) > 200:
            raise forms.ValidationError("Product name is too long (max 200 characters).")
        return name
