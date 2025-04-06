from django import forms
from .models import NegotiationMessage

class CounterOfferForm(forms.Form):
    counter_amount = forms.DecimalField(
        label="Your Counter Offer",
        min_value=0,
        required=True,
        widget=forms.NumberInput(attrs={'step': '0.01'})
    )
    counter_delivery_time = forms.IntegerField(
        label="Counter Delivery Time (days)",
        min_value=1,
        required=True)
    message = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4}),
        required=False,
        label="Additional Comments")

class NegotiationMessageForm(forms.ModelForm):
    class Meta:
        model = NegotiationMessage
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 4}),
        }