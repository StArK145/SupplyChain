from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class ManufacturerRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=100, required=True)
    last_name = forms.CharField(max_length=100, required=True)
    company_name = forms.CharField(max_length=200, required=True)
    city = forms.CharField(max_length=100, required=True)
    state = forms.CharField(max_length=100, required=True)
    business_type = forms.CharField(max_length=100, required=True)
    website = forms.URLField(required=False)
    phone_number = forms.CharField(max_length=20, required=True)
    key_products = forms.CharField(widget=forms.Textarea, required=True)
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2',
                  'first_name', 'last_name', 'company_name', 'city', 
                  'state', 'business_type', 'website', 'phone_number', 
                  'key_products')

class ManufacturerLoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)