from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Supplier, Bid, SupplierReview

@admin.register(SupplierReview)
class SupplierReviewAdmin(admin.ModelAdmin):
    list_display = ('supplier', 'manufacturer', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('supplier__company_name', 'manufacturer__company_name', 'comment')

admin.site.register([Supplier, Bid])
