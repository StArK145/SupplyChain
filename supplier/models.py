from django.db import models
from django.contrib.auth.models import User
from manufacturer.models import QuoteRequest
from django.core.validators import MinValueValidator, MaxValueValidator

class Supplier(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    company_name = models.CharField(max_length=200)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    business_type = models.CharField(max_length=100)
    website = models.URLField(blank=True)
    phone_number = models.CharField(max_length=20)
    key_services = models.TextField()
    wallet_address = models.CharField(max_length=42, blank=True, null=True)
    
    review_count = models.PositiveIntegerField(default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    
    def update_review_stats(self):
        reviews = self.reviews.all()
        self.review_count = reviews.count()
        avg = reviews.aggregate(models.Avg('rating'))['rating__avg'] or 0
        self.average_rating = round(avg, 2)
        self.save()

    def __str__(self):
        return self.company_name
    
class Bid(models.Model):
    supplier = models.ForeignKey('Supplier', on_delete=models.CASCADE)
    quote = models.ForeignKey(QuoteRequest, on_delete=models.CASCADE)
    bid_amount = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_time = models.PositiveIntegerField(help_text="Delivery time in days")
    comments = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    feedback_given = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=[
        ('submitted', 'Submitted'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected')
    ], default='submitted')
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('deposited', 'Deposit Received'),
        ('released', 'Payment Released'),
        ('disputed', 'Disputed'),
    ]
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending'
    )
    transaction_hash = models.CharField(max_length=66, blank=True, null=True)
    TRANSPORT_CHOICES = [
        ('road', 'Road Transport'),
        ('air', 'Air Transport'),
    ]
    
    VEHICLE_CHOICES = [
        ('small_truck', 'Small Truck (3.5-7.5 tons)'),
        ('medium_truck', 'Medium Truck (7.5-16 tons)'),
        ('large_truck', 'Large Truck (16-32 tons)'),
        ('articulated_truck', 'Articulated Truck (>32 tons)'),
    ]
    
    AIRCRAFT_CHOICES = [
        ('cargo_plane', 'Cargo Plane'),
        ('passenger_plane', 'Passenger Plane (Cargo Hold)'),
    ]
    
    transport_mode = models.CharField(
        max_length=20,
        choices=TRANSPORT_CHOICES,
        default='road'
    )
    
    # Road transport fields
    vehicle_type = models.CharField(
        max_length=20,
        choices=VEHICLE_CHOICES,
        blank=True,
        null=True
    )
    vehicle_count = models.PositiveIntegerField(
        blank=True,
        null=True
    )
    load_percentage = models.PositiveIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(100)]
    )
    empty_return = models.BooleanField(default=False)
    
    # Air transport fields
    aircraft_type = models.CharField(
        max_length=20,
        choices=AIRCRAFT_CHOICES,
        blank=True,
        null=True
    )
    flight_count = models.PositiveIntegerField(
        blank=True,
        null=True
    )
    
    # Calculated fields
    calculated_emissions = models.FloatField(null=True, blank=True)  # kg CO2
    distance_km = models.FloatField(null=True, blank=True)    

    def get_negotiation_status(self):
        if hasattr(self, 'negotiation'):
            return self.negotiation.get_status_display()
        return "No negotiation"

    def __str__(self):
        return f"Bid for {self.quote.product} by {self.supplier.company_name}"
    


# Add to supplier/models.py
class SupplierReview(models.Model):
    RATING_CHOICES = [
        (1, 'Poor'),
        (2, 'Fair'),
        (3, 'Good'),
        (4, 'Very Good'),
        (5, 'Excellent'),
    ]
    
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='reviews')
    manufacturer = models.ForeignKey('manufacturer.Manufacturer', on_delete=models.CASCADE)
    bid = models.OneToOneField('Bid', on_delete=models.CASCADE, related_name='review')
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    
    # Add to SupplierReview model in supplier/models.py
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.supplier.update_review_stats()
        
    def __str__(self):
        return f"Review for {self.supplier.company_name} by {self.manufacturer.company_name}"