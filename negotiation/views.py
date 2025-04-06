from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from .models import Negotiation, NegotiationMessage
from .forms import CounterOfferForm, NegotiationMessageForm
from supplier.models import Bid
from manufacturer.models import Manufacturer
from utils.email import send_email
from django.urls import reverse

@login_required
def start_negotiation(request, bid_id):
    bid = get_object_or_404(Bid, id=bid_id)
    
    # Check if user is the manufacturer who owns the quote
    if not hasattr(request.user, 'manufacturer') or bid.quote.manufacturer.user != request.user:
        messages.error(request, "You don't have permission to negotiate this bid")
        return redirect('manufacturer_dashboard')
    
    # Check if negotiation already exists
    if hasattr(bid, 'negotiation'):
        return redirect('view_negotiation', negotiation_id=bid.negotiation.id)
    
    # Create new negotiation
    negotiation = Negotiation.objects.create(
        bid=bid,
        expiry_date=timezone.now() + timedelta(days=7)  # 7 days to negotiate
    )
    
    # Create initial message
    NegotiationMessage.objects.create(
        negotiation=negotiation,
        sender=request.user,
        message=f"Manufacturer has initiated negotiation for bid amount {bid.bid_amount} {bid.quote.currency}"
    )
    
    # Notify supplier
    send_email(
        subject=f"Negotiation Started for {bid.quote.product}",
        to_email=bid.supplier.user.email,
        template_name="emails/negotiation_started.html",
        context={
            'supplier': bid.supplier,
            'manufacturer': bid.quote.manufacturer,
            'quote': bid.quote,
            'bid': bid,
            'negotiation': negotiation
        }
    )
    
    messages.success(request, 'Negotiation started successfully!')
    return redirect('view_negotiation', negotiation_id=negotiation.id)

@login_required
def view_negotiation(request, negotiation_id):
    negotiation = get_object_or_404(Negotiation, id=negotiation_id)
    bid = negotiation.bid
    
    # Check if user is authorized (either manufacturer or supplier)
    if not (request.user == bid.supplier.user or request.user == bid.quote.manufacturer.user):
        messages.error(request, "You don't have permission to view this negotiation")
        return redirect('home')
    
    # Mark unread messages as read for current user
    negotiation.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)
    
    if request.method == 'POST':
        if request.user == bid.supplier.user:
            form = NegotiationMessageForm(request.POST)
        else:
            form = CounterOfferForm(request.POST)
        
        if form.is_valid():
            if request.user == bid.supplier.user:
                # Supplier is sending a regular message
                message = form.save(commit=False)
                message.negotiation = negotiation
                message.sender = request.user
                message.save()
                
                # Notify manufacturer
                send_email(
                    subject=f"New Message in Negotiation for {bid.quote.product}",
                    to_email=bid.quote.manufacturer.user.email,
                    template_name="emails/negotiation_message.html",
                    context={
                        'manufacturer': bid.quote.manufacturer,
                        'supplier': bid.supplier,
                        'quote': bid.quote,
                        'bid': bid,
                        'negotiation': negotiation,
                        'message': message
                    }
                )
            else:
                # Manufacturer is making a counter offer
                counter_amount = form.cleaned_data['counter_amount']
                counter_delivery_time = form.cleaned_data['counter_delivery_time']
                message_text = form.cleaned_data['message']
                
                message = NegotiationMessage.objects.create(
                    negotiation=negotiation,
                    sender=request.user,
                    message=message_text or f"Counter offer: {counter_amount} {bid.quote.currency}, Delivery in {counter_delivery_time} days",
                    counter_amount=counter_amount,
                    counter_delivery_time=counter_delivery_time
                )
                
                # Notify supplier
                send_email(
                    subject=f"Counter Offer Received for {bid.quote.product}",
                    to_email=bid.supplier.user.email,
                    template_name="emails/counter_offer_received.html",
                    context={
                        'supplier': bid.supplier,
                        'manufacturer': bid.quote.manufacturer,
                        'quote': bid.quote,
                        'bid': bid,
                        'negotiation': negotiation,
                        'message': message
                    }
                )
            
            messages.success(request, 'Message sent successfully!')
            return redirect('view_negotiation', negotiation_id=negotiation.id)
    else:
        if request.user == bid.supplier.user:
            form = NegotiationMessageForm()
        else:
            form = CounterOfferForm()
    
    context = {
        'negotiation': negotiation,
        'bid': bid,
        'messages': negotiation.messages.all().order_by('created_at'),
        'form': form,
        'is_supplier': request.user == bid.supplier.user,
        'is_manufacturer': request.user == bid.quote.manufacturer.user,
        'now': timezone.now()
    }
    
    return render(request, 'negotiation/detail.html', context)

@login_required
def accept_negotiation(request, negotiation_id):
    negotiation = get_object_or_404(Negotiation, id=negotiation_id)
    bid = negotiation.bid
    
    # Check if user is the manufacturer
    if not hasattr(request.user, 'manufacturer') or bid.quote.manufacturer.user != request.user:
        messages.error(request, "You don't have permission to accept this negotiation")
        return redirect('home')
    
    if negotiation.status != 'active':
        messages.error(request, "This negotiation is no longer active")
        return redirect('view_negotiation', negotiation_id=negotiation.id)
    
    # Update negotiation status
    negotiation.status = 'accepted'
    negotiation.save()
    
    # Update bid with final negotiated terms (use last counter offer if exists)
    last_counter = negotiation.messages.filter(counter_amount__isnull=False).last()
    if last_counter:
        bid.bid_amount = last_counter.counter_amount
        bid.delivery_time = last_counter.counter_delivery_time
    bid.status = 'accepted'
    bid.save()
    
    # Update quote
    quote = bid.quote
    quote.accepted_bid = bid
    quote.status = 'awarded'
    quote.save()
    
    # Get supplier's wallet address
    supplier_wallet_address = bid.supplier.wallet_address
    
    if not supplier_wallet_address:
        messages.warning(request, "Supplier hasn't set a wallet address yet. Please ask them to complete their profile.")
        return redirect('view_negotiation', negotiation_id=negotiation.id)
    
    # Redirect to payment gateway with necessary parameters
    return redirect(reverse('payment_gateway') + f'?supplier_address={supplier_wallet_address}&amount={bid.bid_amount}&supplier_name={bid.supplier.company_name}')

@login_required
def reject_negotiation(request, negotiation_id):
    negotiation = get_object_or_404(Negotiation, id=negotiation_id)
    bid = negotiation.bid
    
    # Check if user is authorized (either party can reject)
    if request.user not in [bid.supplier.user, bid.quote.manufacturer.user]:
        messages.error(request, "You don't have permission to reject this negotiation")
        return redirect('home')
    
    if negotiation.status != 'active':
        messages.error(request, "This negotiation is no longer active")
        return redirect('view_negotiation', negotiation_id=negotiation.id)
    
    # Update negotiation status
    negotiation.status = 'rejected'
    negotiation.save()
    
    # Update bid status
    bid.status = 'rejected'
    bid.save()
    
    # Notify other party
    if request.user == bid.supplier.user:
        recipient = bid.quote.manufacturer.user
    else:
        recipient = bid.supplier.user
    
    send_email(
        subject=f"Negotiation Rejected for {bid.quote.product}",
        to_email=recipient.email,
        template_name="emails/negotiation_rejected.html",
        context={
            'recipient': recipient,
            'sender': request.user,
            'quote': bid.quote,
            'bid': bid,
            'negotiation': negotiation
        }
    )
    
    messages.success(request, 'Negotiation rejected!')
    return redirect('supplier_dashboard' if hasattr(request.user, 'supplier') else 'manufacturer_dashboard')  