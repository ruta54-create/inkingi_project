# forms.py

from django import forms
from django.template import loader
from django.conf import settings
from django.core.mail import send_mail as django_send_mail

from django.contrib.auth.forms import PasswordResetForm
from .utils import send_smtp_email

USER_TYPE_CHOICES = (
    ('customer', 'Customer'),
    ('vendor', 'Vendor/Seller'),
)

class RegistrationForm(forms.Form):
    username = forms.CharField(max_length=18, widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'username'
    }))
    email = forms.EmailField(max_length=25, widget=forms.EmailInput(attrs={
        'class': 'form-control', 'placeholder': 'you@example.com'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control', 'placeholder': 'Password'
    }))
    password_confirm = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control', 'placeholder': 'Confirm Password'
    })) 
    
    user_type = forms.ChoiceField(
        choices=USER_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Account Type"
    )
    
    phone = forms.CharField(max_length=20, required=False)
    location = forms.CharField(max_length=100, required=False)

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError(
                "Password and Confirm Password fields do not match."
            )
        return cleaned_data


class LoginForm(forms.Form):
    email = forms.CharField(
        max_length=254,
        label='Email or Username',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'you@example.com'
        })
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password'
        })
    )


class ProfileForm(forms.Form):
    username = forms.CharField(max_length=18, widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'username'
    }))
    email = forms.EmailField(max_length=254, widget=forms.EmailInput(attrs={
        'class': 'form-control', 'placeholder': 'you@example.com'
    }))
    phone = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    location = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))


class SMTPPasswordResetForm(PasswordResetForm):
    """PasswordResetForm that uses raw SMTP sender when available.

    Falls back to Django's send_mail (e.g., locmem backend during tests)
    if EMAIL_BACKEND appears to be a Django backend that is not external SMTP.
    """
    def send_mail(self, subject_template_name, email_template_name,
                  context, from_email, to_email, html_email_template_name=None):
        
        subject = loader.render_to_string(subject_template_name, context)
    
        subject = ''.join(subject.splitlines())
        body = loader.render_to_string(email_template_name, context)
        html_message = None
        if html_email_template_name:
            html_message = loader.render_to_string(html_email_template_name, context)

        email_backend = getattr(settings, 'EMAIL_BACKEND', '') or ''
        if 'locmem' in email_backend or email_backend.startswith('django.core.mail.backends.locmem'):
            django_send_mail(subject, body, from_email, [to_email], html_message=html_message)
            return

        
        try:
            send_smtp_email(to_email, subject, body, html_message=html_message, from_email=from_email)
        except Exception:
            
            django_send_mail(subject, body, from_email, [to_email], html_message=html_message)