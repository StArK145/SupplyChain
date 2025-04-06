from django.contrib import admin
from .models import Manufacturer, QuoteRequest

@admin.register(Manufacturer)
class ManufacturerAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'user', 'city', 'state', 'business_type')
    list_filter = ('state', 'business_type')
    search_fields = ('company_name', 'user__username', 'city')
    raw_id_fields = ('user',)
    ordering = ('company_name',)

@admin.register(QuoteRequest)
class QuoteRequestAdmin(admin.ModelAdmin):
    list_display = ('product', 'manufacturer', 'category', 'status', 'deadline', 'created_at')
    list_filter = ('status', 'category', 'created_at')
    search_fields = ('product', 'manufacturer__company_name', 'description')
    raw_id_fields = ('manufacturer', 'accepted_bid')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)