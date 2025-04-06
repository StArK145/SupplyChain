# manufacturer/urls.py
from django.urls import path
from . import views
from .views import calculate_carbon_footprint

urlpatterns = [
    # Authentication URLs
    path('register/', views.manufacturer_register, name='manufacturer_register'),
    path('login/', views.manufacturer_login, name='manufacturer_login'),
    
    # Dashboard and Action URLs
    path('dashboard/', views.manufacturer_dashboard, name='manufacturer_dashboard'),
    path('request-quote/', views.request_quote, name='manufacturer_request_quote'),
    path('list-products/', views.list_products, name='manufacturer_list_products'),
    path('complete-profile/', views.complete_profile, name='manufacturer_complete_profile'),
    path('quote-history/', views.quote_history, name='manufacturer_quote_history'),
    path('quote-bids/<int:quote_id>/', views.view_quote_bids, name='view_quote_bids'),
    path('profile/', views.view_profile, name='manufacturer_profile'),
    path('profile/edit/', views.edit_profile, name='manufacturer_edit_profile'),
    path('accept-bid/<int:bid_id>/', views.accept_bid, name='accept_bid'),
    path('direct-accept-bid/<int:bid_id>/', views.accept_bid, name='direct_accept_bid'),
    path('supplier-profile/<int:supplier_id>/', views.view_supplier_profile, name='view_supplier_profile'),
    path('commodity-price/', views.get_commodity_price, name='commodity_price'),
    path('analyze-supplier/<int:supplier_id>/', views.analyze_supplier, name='analyze_supplier'),
    path('calculate-carbon-footprint/', calculate_carbon_footprint, name='calculate_carbon_footprint'),
]