from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from manufacturer.models import QuoteRequest

class SupplierRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=100, required=True)
    last_name = forms.CharField(max_length=100, required=True)
    company_name = forms.CharField(max_length=200, required=True)
    city = forms.CharField(max_length=100, required=True)
    state = forms.CharField(max_length=100, required=True)
    business_type = forms.CharField(max_length=100, required=True)
    website = forms.URLField(required=False)
    phone_number = forms.CharField(max_length=20, required=True)
    key_services = forms.CharField(widget=forms.Textarea, required=True)
    email = forms.EmailField(required=True)
    wallet_address = forms.CharField(max_length=42, required=True, 
                                   label="Ethereum Wallet Address (0x...)")

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2',
                  'first_name', 'last_name', 'company_name', 'city', 
                  'state', 'business_type', 'website', 'phone_number', 
                  'key_services', 'wallet_address')

class SupplierLoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)


# class BidForm(forms.Form):
#     bid_amount = forms.DecimalField(label="Your Price", min_value=0)
#     delivery_time = forms.IntegerField(label="Delivery Time (days)", min_value=1)
#     comments = forms.CharField(widget=forms.Textarea, required=False)

# supplier/forms.py
from django import forms
from .models import Bid

class BidForm(forms.ModelForm):
    transport_mode = forms.ChoiceField(
        choices=Bid.TRANSPORT_CHOICES,
        initial='road',
        widget=forms.RadioSelect
    )
    vehicle_type = forms.ChoiceField(
        choices=Bid.VEHICLE_CHOICES,
        required=False
    )
    vehicle_count = forms.IntegerField(
        min_value=1,
        required=False,
        initial=1
    )
    load_percentage = forms.IntegerField(
        min_value=1,
        max_value=100,
        required=False,
        initial=100
    )
    empty_return = forms.BooleanField(
        required=False,
        initial=False
    )
    aircraft_type = forms.ChoiceField(
        choices=Bid.AIRCRAFT_CHOICES,
        required=False
    )
    flight_count = forms.IntegerField(
        min_value=1,
        required=False,
        initial=1
    )

    class Meta:
        model = Bid
        fields = [
            'bid_amount', 
            'delivery_time', 
            'comments',
            'transport_mode',
            'vehicle_type',
            'vehicle_count',
            'load_percentage',
            'empty_return',
            'aircraft_type',
            'flight_count'
        ]
        widgets = {
            'comments': forms.Textarea(attrs={'rows': 4}),
        }
        
    def clean(self):
        cleaned_data = super().clean()
        transport_mode = cleaned_data.get('transport_mode')
        
        if transport_mode == 'road':
            if not cleaned_data.get('vehicle_type'):
                self.add_error('vehicle_type', 'This field is required for road transport')
            if not cleaned_data.get('vehicle_count'):
                self.add_error('vehicle_count', 'This field is required for road transport')
            if not cleaned_data.get('load_percentage'):
                self.add_error('load_percentage', 'This field is required for road transport')
        
        elif transport_mode == 'air':
            if not cleaned_data.get('aircraft_type'):
                self.add_error('aircraft_type', 'This field is required for air transport')
            if not cleaned_data.get('flight_count'):
                self.add_error('flight_count', 'This field is required for air transport')
        
        return cleaned_data

# Add to supplier/forms.py
from django import forms
from .models import SupplierReview

from django import forms

class ReviewForm(forms.ModelForm):
    # Define rating choices (1-5 with labels)
    RATING_CHOICES = [
        (1, 'Poor'),
        (2, 'Fair'),
        (3, 'Good'),
        (4, 'Very Good'),
        (5, 'Excellent'),
    ]
    
    # Override the rating field to use RadioSelect with our choices
    rating = forms.ChoiceField(
        choices=RATING_CHOICES,
        widget=forms.RadioSelect,
        required=True
    )
    
    class Meta:
        model = SupplierReview
        fields = ['rating', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 4}),
        }