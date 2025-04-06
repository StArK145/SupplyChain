from manufacturer.models import QuoteRequest
from .models import Supplier, Bid
from .forms import BidForm
from .models import SupplierReview, Bid
from .forms import ReviewForm
from django.shortcuts import get_object_or_404, redirect
from negotiation.forms import CounterOfferForm
from negotiation.models import Negotiation, NegotiationMessage
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from .forms import SupplierRegistrationForm, SupplierLoginForm, BidForm, ReviewForm
from .models import Supplier, Bid, SupplierReview
from django.contrib.auth.models import User
from manufacturer.models import QuoteRequest, Manufacturer
from django.contrib import messages

# Add at the top
from django.conf import settings
from utils.email import send_email
from django.db.models import Avg
from django.contrib.auth.decorators import login_required
from django.utils import timezone

import json
import math
import requests
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from geopy.distance import great_circle
from geopy.geocoders import Nominatim
from django.conf import settings
from collections import defaultdict
from utils.route_calculator import RouteFinder
import math


def supplier_register(request):
    if request.method == 'POST':
        form = SupplierRegistrationForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password1']
            )

            supplier = Supplier.objects.create(
                user=user,
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                company_name=form.cleaned_data['company_name'],
                city=form.cleaned_data['city'],
                state=form.cleaned_data['state'],
                business_type=form.cleaned_data['business_type'],
                website=form.cleaned_data['website'],
                phone_number=form.cleaned_data['phone_number'],
                key_services=form.cleaned_data['key_services'],
                wallet_address=form.cleaned_data['wallet_address']
            )

            # Send welcome email
            send_email(
                subject="Your Supplier Account Has Been Created",
                to_email=user.email,
                template_name="emails/account_created_supplier.html",
                context={
                    'supplier': supplier,
                    'user': user
                }
            )

            # Log the user in after registration
            authenticated_user = authenticate(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password1']
            )
            if authenticated_user is not None:
                login(request, authenticated_user)

            messages.success(request, 'Supplier registered successfully!')
            # Redirect to dashboard after successful registration
            return redirect('supplier_dashboard')
    else:
        form = SupplierRegistrationForm()
    return render(request, 'supplier/register.html', {'form': form})


def supplier_login(request):
    if request.method == 'POST':
        form = SupplierLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)

            if user is not None:
                # Check if this user is a supplier
                try:
                    supplier = Supplier.objects.get(user=user)
                    login(request, user)
                    return redirect('supplier_dashboard')
                except Supplier.DoesNotExist:
                    form.add_error(
                        None, "This account is not registered as a supplier")
    else:
        form = SupplierLoginForm()
    return render(request, 'supplier/login.html', {'form': form})

# supplier/views.py


def supplier_dashboard(request):
    if not request.user.is_authenticated:
        return redirect('supplier_login')

    try:
        supplier = Supplier.objects.get(user=request.user)
        open_quotes = QuoteRequest.objects.filter(
            status='open').order_by('-created_at')
        reviews = supplier.reviews.all()
        average_rating = reviews.aggregate(Avg('rating'))['rating__avg']
        negotiations = Negotiation.objects.filter(
            bid__supplier=supplier,
            status='active'
        ).select_related('bid', 'bid__quote')[:5]  # Show only 5 most recent

        # Category filtering
        category_filter = request.GET.get('category')
        if category_filter:
            open_quotes = open_quotes.filter(category=category_filter)

        your_bids = Bid.objects.filter(
            supplier=supplier).select_related('quote')

        return render(request, 'supplier/dashboard.html', {
            'supplier': supplier,
            'open_quotes': open_quotes,
            'your_bids': your_bids,
            'negotiations': negotiations,
            'categories': QuoteRequest.objects.values_list('category', flat=True).distinct(),
            'current_category': category_filter,
            'now': timezone.now(),
            'average_rating': average_rating,
            'review_count': reviews.count()
        })
    except Supplier.DoesNotExist:
        return redirect('supplier_login')


# supplier/views.py


def submit_bid(request, quote_id):
    if not request.user.is_authenticated:
        return redirect('supplier_login')

    supplier = get_object_or_404(Supplier, user=request.user)
    quote = get_object_or_404(QuoteRequest, id=quote_id, status='open')

    if request.method == 'POST':
        form = BidForm(request.POST)
        if form.is_valid():
            try:
                bid = form.save(commit=False)
                bid.supplier = supplier
                bid.quote = quote

                # Save transport details
                bid.transport_mode = form.cleaned_data['transport_mode']
                if bid.transport_mode == 'road':
                    bid.vehicle_type = form.cleaned_data['vehicle_type']
                    bid.vehicle_count = form.cleaned_data['vehicle_count']
                    bid.load_percentage = form.cleaned_data['load_percentage']
                    bid.empty_return = form.cleaned_data['empty_return']
                else:  # air transport
                    bid.aircraft_type = form.cleaned_data['aircraft_type']
                    bid.flight_count = form.cleaned_data['flight_count']

                bid.save()

                # Send bid confirmation to supplier
                send_email(
                    subject=f"Your Bid for {quote.product} Has Been Submitted",
                    to_email=request.user.email,
                    template_name="emails/bid_submitted.html",
                    context={
                        'supplier': supplier,
                        'quote': quote,
                        'bid': bid
                    }
                )

                # Send notification to manufacturer
                send_email(
                    subject=f"New Bid Received for {quote.product}",
                    to_email=quote.manufacturer.user.email,
                    template_name="emails/new_bid_received.html",
                    context={
                        'manufacturer': quote.manufacturer,
                        'supplier': supplier,
                        'quote': quote,
                        'bid': bid
                    }
                )

                messages.success(
                    request, 'Your bid has been submitted successfully!')
                return redirect('supplier_dashboard')

            except Exception as e:
                messages.error(request, f'Error submitting bid: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors in the form.')
    else:
        form = BidForm()

    return render(request, 'supplier/submit_bid.html', {
        'form': form,
        'quote': quote,
        'supplier': supplier
    })


def view_profile(request):
    if not request.user.is_authenticated:
        return redirect('supplier_login')

    supplier = Supplier.objects.get(user=request.user)
    reviews = supplier.reviews.all()
    # average_rating = reviews.aggregate(models.Avg('rating'))['rating__avg']
    average_rating = reviews.aggregate(Avg('rating'))['rating__avg']

    return render(request, 'supplier/profile.html', {
        'supplier': supplier,
        'reviews': reviews,
        'average_rating': average_rating,
        'review_count': reviews.count()
    })


def edit_profile(request):
    if not request.user.is_authenticated:
        return redirect('supplier_login')

    try:
        supplier = Supplier.objects.get(user=request.user)
    except Supplier.DoesNotExist:
        messages.error(request, "Supplier profile not found")
        return redirect('supplier_dashboard')

    if request.method == 'POST':
        # Get all form data
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        company_name = request.POST.get('company_name')
        city = request.POST.get('city')
        state = request.POST.get('state')
        business_type = request.POST.get('business_type')
        website = request.POST.get('website')
        phone_number = request.POST.get('phone_number')
        key_services = request.POST.get('key_services')
        wallet_address = request.POST.get('wallet_address')

        # Basic validation
        if not all([first_name, last_name, company_name, city, state, business_type, phone_number, key_services, wallet_address]):
            messages.error(request, "All required fields must be filled")
            return render(request, 'supplier/edit_profile.html', {'supplier': supplier})

        # Validate wallet address format
        if not wallet_address.startswith('0x') or len(wallet_address) != 42:
            messages.error(
                request, "Please enter a valid Ethereum wallet address (should start with 0x and be 42 characters long)")
            return render(request, 'supplier/edit_profile.html', {'supplier': supplier})

        # Update supplier fields
        supplier.first_name = first_name
        supplier.last_name = last_name
        supplier.company_name = company_name
        supplier.city = city
        supplier.state = state
        supplier.business_type = business_type
        supplier.website = website
        supplier.phone_number = phone_number
        supplier.key_services = key_services
        supplier.wallet_address = wallet_address

        try:
            supplier.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('supplier_profile')
        except Exception as e:
            messages.error(request, f'Error saving profile: {str(e)}')

    return render(request, 'supplier/edit_profile.html', {'supplier': supplier})


def view_manufacturer_profile(request, manufacturer_id):
    if not request.user.is_authenticated:
        return redirect('supplier_login')

    try:
        supplier = Supplier.objects.get(user=request.user)
        manufacturer = Manufacturer.objects.get(id=manufacturer_id)
        quote_id = request.GET.get('quote_id')  # Get from URL parameter
        return render(request, 'supplier/manufacturer_profile.html', {
            'manufacturer': manufacturer,
            'supplier': supplier,
            'quote_id': quote_id
        })
    except Manufacturer.DoesNotExist:
        messages.error(request, "Manufacturer not found")
        return redirect('supplier_dashboard')


def supplier_negotiations(request):
    if not request.user.is_authenticated:
        return redirect('supplier_login')

    supplier = get_object_or_404(Supplier, user=request.user)
    negotiations = Negotiation.objects.filter(
        bid__supplier=supplier).select_related('bid', 'bid__quote')

    return render(request, 'supplier/negotiations.html', {
        'supplier': supplier,
        'negotiations': negotiations,
        'now': timezone.now()
    })


def supplier_view_negotiation(request, negotiation_id):
    if not request.user.is_authenticated:
        return redirect('supplier_login')

    negotiation = get_object_or_404(Negotiation, id=negotiation_id)
    bid = negotiation.bid

    # Check if user is the supplier for this bid
    if bid.supplier.user != request.user:
        messages.error(
            request, "You don't have permission to view this negotiation")
        return redirect('supplier_dashboard')

    # Mark unread messages as read
    negotiation.messages.filter(is_read=False).exclude(
        sender=request.user).update(is_read=True)

    if request.method == 'POST':
        form = CounterOfferForm(request.POST)
        if form.is_valid():
            # Create new message with counter offer
            message = NegotiationMessage.objects.create(
                negotiation=negotiation,
                sender=request.user,
                message=form.cleaned_data['message'],
                counter_amount=form.cleaned_data['counter_amount'],
                counter_delivery_time=form.cleaned_data['counter_delivery_time']
            )

            # Notify manufacturer
            send_email(
                subject=f"Counter Offer Received for {bid.quote.product}",
                to_email=bid.quote.manufacturer.user.email,
                template_name="emails/counter_offer_received.html",
                context={
                    'manufacturer': bid.quote.manufacturer,
                    'supplier': bid.supplier,
                    'quote': bid.quote,
                    'bid': bid,
                    'negotiation': negotiation,
                    'message': message
                }
            )

            messages.success(request, 'Counter offer submitted successfully!')
            return redirect('supplier_view_negotiation', negotiation_id=negotiation.id)
    else:
        form = CounterOfferForm()

    return render(request, 'supplier/view_negotiation.html', {
        'negotiation': negotiation,
        'bid': bid,
        'messages': negotiation.messages.all().order_by('created_at'),
        'form': form,
        'now': timezone.now()
    })


# Add to supplier/views.py


def submit_review(request, bid_id):
    if not request.user.is_authenticated or not hasattr(request.user, 'manufacturer'):
        return redirect('manufacturer_login')

    bid = get_object_or_404(Bid, id=bid_id)

    # Check if the current user is the manufacturer who accepted this bid
    if bid.quote.manufacturer.user != request.user or bid.status != 'accepted':
        messages.error(request, "You can't review this bid")
        return redirect('manufacturer_dashboard')

    # Check if review already exists
    if hasattr(bid, 'review'):
        messages.info(
            request, "You've already reviewed this supplier for this bid")
        return redirect('manufacturer_dashboard')

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.supplier = bid.supplier
            review.manufacturer = bid.quote.manufacturer
            review.bid = bid
            review.save()

            # Mark that feedback has been given
            bid.feedback_given = True
            bid.save()

            # Send email notification to supplier
            send_email(
                subject=f"New Review Received from {review.manufacturer.company_name}",
                to_email=review.supplier.user.email,
                template_name="emails/new_review_received.html",
                context={
                    'supplier': review.supplier,
                    'manufacturer': review.manufacturer,
                    'review': review,
                    'bid': bid
                }
            )

            messages.success(request, 'Thank you for your feedback!')
            # return redirect('manufacturer_dashboard')
            return redirect('manufacturer_quote_history')
    else:
        form = ReviewForm()

    return render(request, 'supplier/submit_review.html', {
        'form': form,
        'bid': bid,
        'supplier': bid.supplier
    })


@csrf_exempt
@require_POST
def calculate_route(request):
    try:
        data = json.loads(request.body)

        # Get data from request
        supplier_city = data['supplier_city']
        supplier_state = data['supplier_state']
        manufacturer_city = data['manufacturer_city']
        manufacturer_state = data['manufacturer_state']
        transport_mode = data['transport_mode']
        lead_time = data['lead_time']

        # Create addresses
        supplier_address = f"{supplier_city}, {supplier_state}"
        manufacturer_address = f"{manufacturer_city}, {manufacturer_state}"

        # Calculate route
        route_finder = RouteFinder()
        route_details = route_finder.calculate_route_details(
            start_addr=supplier_address,
            end_addr=manufacturer_address,
            transport_mode=transport_mode,
            lead_time_days=lead_time
        )

        if not route_details:
            return JsonResponse({
                'success': False,
                'error': 'Could not calculate route details'
            }, status=400)

        # Format response for road transport
        if route_details['mode'] == 'road':
            # Process detailed route steps
            route_steps = []
            step_types = defaultdict(int)

            for step in route_details['steps']:
                instruction = step['instruction'].replace('Head', 'Continue')
                distance = step['distance']

                # Classify step type
                if 'highway' in instruction.lower() or 'motorway' in instruction.lower():
                    step_type = 'highway'
                elif 'left' in instruction.lower():
                    step_type = 'left_turn'
                elif 'right' in instruction.lower():
                    step_type = 'right_turn'
                elif 'roundabout' in instruction.lower():
                    step_type = 'roundabout'
                else:
                    step_type = 'regular'

                step_types[step_type] += 1

                route_steps.append({
                    'instruction': instruction,
                    'distance': f"{distance}m",
                    'type': step_type
                })

            # Generate route summary
            highway_percentage = (
                step_types['highway'] / len(route_steps)) * 100
            route_summary = (
                f"Route includes {len(route_steps)} steps: "
                f"{step_types['highway']} highway sections ({highway_percentage:.0f}%), "
                f"{step_types['left_turn']} left turns, "
                f"{step_types['right_turn']} right turns"
            )

            # Generate detailed directions
            detailed_directions = "\n".join(
                [f"{i+1}. {step['instruction']} ({step['distance']})"
                 for i, step in enumerate(route_steps)])

            response_data = {
                'success': True,
                'mode': 'road',
                'distance': route_details['distance'],
                'transit_time': route_details['transit_time'],
                'route_summary': route_summary,
                'detailed_directions': detailed_directions,
                'total_steps': len(route_steps),
                'highway_percentage': round(highway_percentage),
                'total_days': route_details['total_days'],
                'delivery_days': route_details['delivery_days']
            }

        # Format response for air transport
        else:
            response_data = {
                'success': True,
                'mode': 'air',
                'distance': route_details['distance'],
                'transit_time': route_details['transit_time'],
                'route_description': f"{supplier_city} Airport → {manufacturer_city} Airport",
                'total_days': route_details['total_days'],
                'delivery_days': route_details['delivery_days']
            }

        return JsonResponse(response_data)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
