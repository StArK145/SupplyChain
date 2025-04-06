from django.urls import path
from . import views
from manufacturer.views import payment_gateway_view 

urlpatterns = [
    path('start/<int:bid_id>/', views.start_negotiation, name='start_negotiation'),
    path('<int:negotiation_id>/', views.view_negotiation, name='view_negotiation'),
    path('<int:negotiation_id>/accept/', views.accept_negotiation, name='accept_negotiation'),
    path('<int:negotiation_id>/reject/', views.reject_negotiation, name='reject_negotiation'),
    path('payment-gateway/', payment_gateway_view, name='payment_gateway'),
]