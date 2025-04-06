from django.db import models
from supplier.models import Supplier, Bid
from manufacturer.models import Manufacturer, QuoteRequest
from django.utils import timezone

class Negotiation(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
    ]
    
    bid = models.OneToOneField(Bid, on_delete=models.CASCADE, related_name='negotiation')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expiry_date = models.DateTimeField()

    def __str__(self):
        return f"Negotiation for {self.bid.quote.product}"

class NegotiationMessage(models.Model):
    negotiation = models.ForeignKey(Negotiation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    message = models.TextField()
    counter_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    counter_delivery_time = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Message from {self.sender.username} at {self.created_at}"