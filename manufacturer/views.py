from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib import messages
from .forms import ManufacturerRegistrationForm, ManufacturerLoginForm
from .models import Manufacturer, QuoteRequest
from supplier.models import Supplier
from django.contrib.auth.models import User
import json
from django.conf import settings
from utils.email import send_email

from django.db.models import Avg  # Add this import

from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from utils.carbon_calculator import CarbonEmissionsCalculator

def manufacturer_register(request):
    if request.method == 'POST':
        form = ManufacturerRegistrationForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password1']
            )
            
            manufacturer = Manufacturer.objects.create(
                user=user,
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                company_name=form.cleaned_data['company_name'],
                city=form.cleaned_data['city'],
                state=form.cleaned_data['state'],
                business_type=form.cleaned_data['business_type'],
                website=form.cleaned_data['website'],
                phone_number=form.cleaned_data['phone_number'],
                key_products=form.cleaned_data['key_products']
            )
            
            # Send welcome email
            send_email(
                subject="Your Manufacturer Account Has Been Created",
                to_email=user.email,
                template_name="emails/account_created_manufacturer.html",
                context={
                    'manufacturer': manufacturer,
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
            
            # Add success message and redirect
            messages.success(request, 'Manufacturer registered successfully!')
            return redirect('manufacturer_dashboard')
            
    else:
        form = ManufacturerRegistrationForm()
    return render(request, 'manufacturer/register.html', {'form': form})


def manufacturer_login(request):
    if request.method == 'POST':
        form = ManufacturerLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                # Check if this user is a manufacturer
                try:
                    manufacturer = Manufacturer.objects.get(user=user)
                    login(request, user)
                    return redirect('manufacturer_dashboard')
                except Manufacturer.DoesNotExist:
                    form.add_error(None, "This account is not registered as a manufacturer")
    else:
        form = ManufacturerLoginForm()
    return render(request, 'manufacturer/login.html', {'form': form})


from supplier.models import Bid
def manufacturer_dashboard(request):
    if not request.user.is_authenticated:
        return redirect('manufacturer_login')
    
    try:
        manufacturer = Manufacturer.objects.get(user=request.user)
        return render(request, 'manufacturer/dashboard.html', {
            'manufacturer': manufacturer
        })
    except Manufacturer.DoesNotExist:
        return redirect('manufacturer_login')

from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from supplier.models import Bid
from utils.email import send_email

def accept_bid(request, bid_id):
    if not request.user.is_authenticated:
        return redirect('manufacturer_login')
    
    try:
        bid = get_object_or_404(Bid, id=bid_id)
        quote = bid.quote
        
        # Check if the current user owns the quote
        if quote.manufacturer.user != request.user:
            messages.error(request, "You don't have permission to manage this bid")
            return redirect('manufacturer_dashboard')
        
        # Check if this bid already has a negotiation
        if hasattr(bid, 'negotiation'):
            # If negotiation exists, redirect to view it
            messages.info(request, "This bid is already in negotiation")
            return redirect('view_negotiation', negotiation_id=bid.negotiation.id)
        
        # Check if the quote already has an accepted bid
        if quote.accepted_bid and quote.accepted_bid != bid:
            messages.error(request, "This quote already has an accepted bid")
            return redirect('view_quote_bids', quote_id=quote.id)
        
        # Since this is the direct-accept-bid URL, we'll treat it as direct acceptance
        # Direct acceptance without negotiation
        bid.status = 'accepted'
        bid.save()
        
        # Update quote status
        quote.status = 'awarded'
        quote.accepted_bid = bid
        quote.save()
        
        # Reject other bids for this quote
        Bid.objects.filter(quote=quote).exclude(id=bid_id).update(status='rejected')
        
        # Send notification to supplier
        send_email(
            subject=f"Your Bid for {quote.product} Has Been Accepted",
            to_email=bid.supplier.user.email,
            template_name="emails/bid_status_update.html",
            context={
                'supplier': bid.supplier,
                'manufacturer': quote.manufacturer,
                'quote': quote,
                'bid': bid
            }
        )
        
        # Send notifications to rejected suppliers
        rejected_bids = Bid.objects.filter(quote=quote, status='rejected')
        for rejected_bid in rejected_bids:
            send_email(
                subject=f"Your Bid for {quote.product} Has Been Rejected",
                to_email=rejected_bid.supplier.user.email,
                template_name="emails/bid_status_update.html",
                context={
                    'supplier': rejected_bid.supplier,
                    'manufacturer': quote.manufacturer,
                    'quote': quote,
                    'bid': rejected_bid
                }
            )
        
        messages.success(request, 'Bid accepted successfully!')
        #return redirect('manufacturer_dashboard')
        return redirect('submit_feedback', bid_id=bid.id)
            
    except Bid.DoesNotExist:
        messages.error(request, 'Bid not found')
        return redirect('manufacturer_dashboard')


def list_products(request):
    if not request.user.is_authenticated:
        return redirect('manufacturer_login')
    return render(request, 'manufacturer/list_products.html', {
        'manufacturer': Manufacturer.objects.get(user=request.user)
    })

def complete_profile(request):
    if not request.user.is_authenticated:
        return redirect('manufacturer_login')
    return render(request, 'manufacturer/complete_profile.html', {
        'manufacturer': Manufacturer.objects.get(user=request.user)
    })



# Update request_quote function
def request_quote(request):
    if not request.user.is_authenticated:
        return redirect('manufacturer_login')
    
    manufacturer = Manufacturer.objects.get(user=request.user)
    
    if request.method == 'POST':
        try:
            # Convert empty strings to None for Decimal fields
            unit_price = request.POST.get('unit_price')
            if unit_price == '':
                unit_price = None
            
            quote = QuoteRequest.objects.create(
                manufacturer=manufacturer,
                product=request.POST.get('product'),
                category=request.POST.get('category'),
                description=request.POST.get('description'),
                deadline=request.POST.get('deadline'),
                quantity=request.POST.get('quantity'),
                unit=request.POST.get('unit'),
                # annual_volume=request.POST.get('annual_volume'),
                # unit_price=unit_price,
                currency=request.POST.get('currency'),
                # shipping_terms=request.POST.get('shipping_terms'),
                # destination_port=request.POST.get('destination_port'),
                # payment_terms=request.POST.get('payment_terms')
            )
            
            # Send quote confirmation email
            send_email(
                subject=f"Your Quote for {quote.product} Has Been Submitted",
                to_email=request.user.email,
                template_name="emails/quote_submitted.html",
                context={
                    'manufacturer': manufacturer,
                    'quote': quote
                }
            )
            
            messages.success(request, 'Your quote request has been submitted successfully!')
            return redirect('manufacturer_quote_history')
        except Exception as e:
            messages.error(request, f'Error submitting request: {str(e)}')
            print(f"Error creating quote: {str(e)}")
    
    return render(request, 'manufacturer/request_quote.html', {
        'manufacturer': manufacturer
    })
# manufacturer/views.py
def quote_history(request):
    if not request.user.is_authenticated:
        return redirect('manufacturer_login')
    
    manufacturer = Manufacturer.objects.get(user=request.user)
    quotes = QuoteRequest.objects.filter(manufacturer=manufacturer).order_by('-created_at')
    
    # Status filtering
    status_filter = request.GET.get('status')
    if status_filter:
        quotes = quotes.filter(status=status_filter)
    
    return render(request, 'manufacturer/quote_history.html', {
        'manufacturer': manufacturer,
        'quotes': quotes
    })
    
def view_profile(request):
    if not request.user.is_authenticated:
        return redirect('manufacturer_login')
    
    manufacturer = Manufacturer.objects.get(user=request.user)
    return render(request, 'manufacturer/profile.html', {'manufacturer': manufacturer})

def edit_profile(request):
    if not request.user.is_authenticated:
        return redirect('manufacturer_login')
    
    manufacturer = Manufacturer.objects.get(user=request.user)
    
    if request.method == 'POST':
        # Update basic fields (no image handling)
        manufacturer.first_name = request.POST.get('first_name', manufacturer.first_name)
        manufacturer.last_name = request.POST.get('last_name', manufacturer.last_name)
        manufacturer.company_name = request.POST.get('company_name', manufacturer.company_name)
        manufacturer.city = request.POST.get('city', manufacturer.city)
        manufacturer.state = request.POST.get('state', manufacturer.state)
        manufacturer.business_type = request.POST.get('business_type', manufacturer.business_type)
        manufacturer.website = request.POST.get('website', manufacturer.website)
        manufacturer.phone_number = request.POST.get('phone_number', manufacturer.phone_number)
        manufacturer.key_products = request.POST.get('key_products', manufacturer.key_products)
        manufacturer.save()
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('manufacturer_profile')
    
    return render(request, 'manufacturer/edit_profile.html', {
        'manufacturer': manufacturer
    })


# manufacturer/views.py
# manufacturer/views.py
def view_quote_bids(request, quote_id):
    if not request.user.is_authenticated:
        return redirect('manufacturer_login')
    
    try:
        manufacturer = Manufacturer.objects.get(user=request.user)
        quote = QuoteRequest.objects.get(id=quote_id, manufacturer=manufacturer)
        bids = Bid.objects.filter(quote=quote).select_related('supplier')
        
        # Pre-calculate average ratings for each supplier
        for bid in bids:
            bid.supplier_avg_rating = bid.supplier.reviews.all().aggregate(Avg('rating'))['rating__avg'] or 0
        
        # Sorting functionality
        sort = request.GET.get('sort', 'newest')
        if sort == 'lowest':
            bids = bids.order_by('bid_amount')
        elif sort == 'highest':
            bids = bids.order_by('-bid_amount')
        elif sort == 'rating':  # New sorting option by rating
            bids = sorted(bids, key=lambda x: x.supplier_avg_rating, reverse=True)
        else:  # default to newest first
            bids = bids.order_by('-submitted_at')
        
        return render(request, 'manufacturer/quote_bids.html', {
            'quote': quote,
            'bids': bids,
            'manufacturer': manufacturer,
            'current_sort': sort  # Pass the current sort option to template
        })
    except (Manufacturer.DoesNotExist, QuoteRequest.DoesNotExist):
        messages.error(request, "Quote not found or you don't have permission to view it")
        return redirect('manufacturer_quote_history')
    
# Update view_supplier_profile in manufacturer/views.py
def view_supplier_profile(request, supplier_id):
    if not request.user.is_authenticated:
        return redirect('manufacturer_login')
    
    try:
        manufacturer = Manufacturer.objects.get(user=request.user)
        supplier = Supplier.objects.get(id=supplier_id)
        quote_id = request.GET.get('quote_id')
        
        # Get reviews and average rating
        reviews = supplier.reviews.all()
        average_rating = reviews.aggregate(Avg('rating'))['rating__avg']
        
        return render(request, 'manufacturer/supplier_profile.html', {
            'supplier': supplier,
            'manufacturer': manufacturer,
            'quote_id': quote_id,
            'reviews': reviews,
            'average_rating': average_rating,
            'review_count': reviews.count()
        })
    except Supplier.DoesNotExist:
        messages.error(request, "Supplier not found")
        return redirect('manufacturer_dashboard')
    
    
from django.http import JsonResponse
from .utils import CommodityPriceFetcher  # Adjust import based on your file location

def get_commodity_price(request):
    """AJAX endpoint to fetch commodity price"""
    commodity = request.GET.get('commodity', '')
    if not commodity:
        return JsonResponse({'error': 'Commodity name required'}, status=400)
    
    fetcher = CommodityPriceFetcher()
    price_data = fetcher.fetch_price(commodity)
    return JsonResponse(price_data)



# manufacturer/views.py
from phi.agent import Agent
from phi.tools.sql import SQLTools
from phi.model.google import Gemini
from django.http import JsonResponse
from supplier.models import Supplier

def analyze_supplier(request, supplier_id):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=403)
    
    try:
        supplier = Supplier.objects.get(id=supplier_id)
        
        # Initialize the agent
        db_url = "sqlite:///db.sqlite3"
        agent = Agent(
            tools=[SQLTools(db_url=db_url)],
            model=Gemini(id="gemini-2.0-flash-exp", temperature=0.4)
        )
        
        # Get the analysis
        response = agent.run(
            f"""Analyze all feedback comments for {supplier.company_name} (ID: {supplier_id}) from the supplier_supplierreview table and provide ONLY the final recommendation based on:
            1. The key points from each feedback
            2. Common themes across all feedbacks
            3. Overall supplier performance assessment
            4. Specific strengths and weaknesses
            5. Areas needing improvement
            
            Present JUST the recommendation in one concise paragraph.
            In the response, always refer to the supplier by their company name ({supplier.company_name}) rather than "Supplier {supplier_id}"."""
        )
        
        return JsonResponse({
            'supplier_name': supplier.company_name,
            'analysis': response.content if response else "No analysis available"
        })
        
    except Supplier.DoesNotExist:
        return JsonResponse({'error': 'Supplier not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
@csrf_exempt
def calculate_carbon_footprint(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=400)
    
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['start_addr', 'end_addr', 'vehicle_type', 'vehicle_count', 'load_percentage']
        for field in required_fields:
            if field not in data or not data[field]:
                return JsonResponse({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }, status=400)
        
        # Convert numeric fields
        try:
            vehicle_count = int(data['vehicle_count'])
            load_percentage = float(data['load_percentage'])
        except (ValueError, TypeError):
            return JsonResponse({
                'success': False,
                'error': 'Invalid vehicle count or load percentage'
            }, status=400)
        
        # Validate values
        if vehicle_count <= 0:
            return JsonResponse({
                'success': False,
                'error': 'Vehicle count must be positive'
            }, status=400)
            
        if load_percentage <= 0 or load_percentage > 100:
            return JsonResponse({
                'success': False,
                'error': 'Load percentage must be between 1 and 100'
            }, status=400)
        
        calculator = CarbonEmissionsCalculator()
        result = calculator.calculate_road_emissions(
            start_addr=data['start_addr'],
            end_addr=data['end_addr'],
            vehicle_type=data['vehicle_type'],
            vehicle_count=vehicle_count,
            load_percentage=load_percentage,
            empty_return=data.get('empty_return', 'false') == 'true'
        )
        
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
    

@login_required
def payment_gateway_view(request):
    supplier_address = request.GET.get('supplier', '')
    amount = request.GET.get('amount', '0')
    negotiation_id = request.GET.get('negotiation_id', '')
    supplier_name = request.GET.get('supplier_name', 'Supplier')
    
    context = {
        'supplier_address': supplier_address,
        'amount': amount,
        'negotiation_id': negotiation_id,
        'supplier_name': supplier_name
    }
    
    return render(request, 'manufacturer/paymentGateway.html', context)