import re

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import User


class RegistrationForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)

    ROLE_CHOICES = (
        ('tenant', 'Tenant — I want to find a room'),
        ('landlord', 'Landlord — I want to list a room'),
    )


    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'role']

    def clean_first_name(self):
        value = self.cleaned_data['first_name']
        if len(value) < 2:
            raise forms.ValidationError('First name must be at least 2 characters.')
        return value

    def clean_last_name(self):
        value = self.cleaned_data['last_name']
        if len(value) < 2:
            raise forms.ValidationError('Last name must be at least 2 characters.')
        return value

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def clean_phone(self):
        phone = self.cleaned_data['phone']
        if not re.match(r'^(97|98)\d{8}$', phone):
            raise forms.ValidationError('Enter a valid Nepal mobile number (e.g. 98XXXXXXXX).')
        return phone

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1:
            if len(password1) < 8:
                self.add_error('password1', 'Password must be at least 8 characters.')
            if not re.search(r'[A-Z]', password1):
                self.add_error('password1', 'Password must contain at least one uppercase letter.')
            if not re.search(r'[0-9]', password1):
                self.add_error('password1', 'Password must contain at least one number.')

        if password1 and password2 and password1 != password2:
            self.add_error('password2', 'Passwords do not match.')

        return cleaned_data


class EmailLoginForm(AuthenticationForm):
    username = forms.EmailField(label='Email')