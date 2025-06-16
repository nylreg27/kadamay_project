# apps/payment/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction # Para sa atomic operations
from django.http import JsonResponse # Para sa AJAX responses
import json # Para sa JSON parsing gikan sa request body
from django.views.decorators.http import require_http_methods # NEW IMPORT: Add this line!

from .forms import PaymentForm
from .models import Payment, Individual, ContributionType # Import necessary models
from apps.family.models import Family # Need to import Family for get_family_details_api_view

# Function-based view for payment creation (from your existing flow)
@login_required
def payment_create_full_form_view(request, individual_id=None):
    individual = None
    if individual_id:
        individual = get_object_or_404(Individual, pk=individual_id)

    if request.method == 'POST':
        form = PaymentForm(request.POST, instance=None) # Always create new instance for new payment
        if form.is_valid():
            payment = form.save(commit=False)
            payment._request_user = request.user # Pass the request user to the model's save method
            
            # --- Handle selected_members_ids from hidden input ---
            selected_members_ids_json = request.POST.get('selected_members_ids', '[]')
            try:
                selected_members_ids = json.loads(selected_members_ids_json)
            except json.JSONDecodeError:
                selected_members_ids = []
            
            # Save the payment instance first to get a PK
            try:
                with transaction.atomic():
                    payment.save()
                    form.save_m2m() # Save M2M for covered_members if used later

                    # Logic to create PaymentIndividualAllocation instances
                    for member_id in selected_members_ids:
                        member = get_object_or_404(Individual, pk=member_id)
                        # For now, we assume allocated_amount is the per-member amount
                        # You might need to refine this if allocation is more complex
                        from .models import PaymentIndividualAllocation # Import here to avoid circular dependency
                        PaymentIndividualAllocation.objects.create(
                            payment=payment,
                            individual=member,
                            allocated_amount=payment.contribution_type.amount if payment.contribution_type else 0 # Use actual contribution amount
                        )

                    messages.success(request, f"Payment record for {payment.individual.full_name} saved successfully!")
                    # Redirect to individual dashboard instead of payment list
                    return redirect(reverse('individual:individual_dashboard', kwargs={'pk': payment.individual.pk}))
            except Exception as e:
                messages.error(request, f"Error saving payment record: {e}")
                # Re-render form with errors if save fails
                context = {
                    'form': form,
                    'page_title': 'Add New Payment',
                    'individual': individual,
                }
                return render(request, 'payment/payment_form.html', context)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        # For GET requests, pre-fill individual if ID is provided
        initial_data = {}
        if individual:
            initial_data['individual'] = individual.pk
        
        form = PaymentForm(initial=initial_data)

    context = {
        'form': form,
        'page_title': 'Add New Payment',
        'individual': individual, # Pass individual object to template for display
    }
    return render(request, 'payment/payment_form.html', context)


# View to display a list of payments (basic placeholder)
@login_required
def payment_list_view(request):
    payments = Payment.objects.all().order_by('-date_paid', '-created_at')
    context = {
        'payments': payments,
        'page_title': 'All Payments'
    }
    return render(request, 'payment/payment_list.html', context) # Assuming you have a payment_list.html

# View to display single payment details (basic placeholder)
@login_required
def payment_detail_view(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    context = {
        'payment': payment,
        'page_title': f'Payment Details: {payment.receipt_number or "N/A"}'
    }
    # This template will be different from individual_dashboard.html
    return render(request, 'payment/payment_detail.html', context)


# === RESTORED: API endpoint for fetching family details (used by payment_form.html) ===
@require_http_methods(["GET"])
@login_required
def get_family_details_api_view(request, individual_id):
    try:
        individual = get_object_or_404(Individual, pk=individual_id)
        family_data = None
        family_members_list = []

        if individual.family:
            family = individual.family
            family_data = {
                'id': family.id,
                'family_name': family.family_name,
                # Add other family details as needed
            }
            # Fetch all members of the family (including the head)
            members = family.members.all().order_by('surname', 'given_name')
            for member in members:
                family_members_list.append({
                    'id': member.id,
                    'full_name': member.full_name,
                    'relationship': member.get_relationship_display_value(), # Use your property/method
                    'status': 'Active' if member.is_active_member and member.is_alive else 'Inactive'
                })

        return JsonResponse({
            'family_name': family_data['family_name'] if family_data else None,
            'family_members': family_members_list
        })
    except Individual.DoesNotExist:
        return JsonResponse({'error': 'Individual not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# === RESTORED: API endpoint for fetching contribution type amount (used by payment_form.html) ===
@require_http_methods(["GET"])
@login_required
def get_contribution_amount_api_view(request, pk):
    try:
        contribution_type = get_object_or_404(ContributionType, pk=pk)
        return JsonResponse({'amount': contribution_type.amount})
    except ContributionType.DoesNotExist:
        return JsonResponse({'error': 'Contribution type not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# === NEW CANCELLATION VIEW ===
@login_required
def cancel_payment_view(request, pk):
    # Ensure it's a POST request for security
    if request.method == 'POST':
        payment = get_object_or_404(Payment, pk=pk)
        
        # Prevent cancelling already cancelled or legacy payments
        if payment.payment_status == 'CANCELLED' or payment.is_legacy_record:
            return JsonResponse({'error': 'This payment cannot be cancelled or is already cancelled/legacy.'}, status=400)

        try:
            # Get cancellation reason from the request body (JSON)
            data = json.loads(request.body)
            cancellation_reason = data.get('cancellation_reason', '').strip()

            if not cancellation_reason:
                return JsonResponse({'error': 'Cancellation reason is required.'}, status=400)
            
            with transaction.atomic():
                payment.is_cancelled = True
                payment.payment_status = 'CANCELLED' # Set status to CANCELLED
                payment.cancellation_reason = cancellation_reason
                payment.cancelled_by = request.user # The user who performed the cancellation
                payment.cancellation_date = timezone.now() # The time of cancellation
                payment.save(update_fields=['is_cancelled', 'payment_status', 'cancellation_reason', 'cancelled_by', 'cancellation_date'])
            
            messages.success(request, f"Payment (OR: {payment.receipt_number or 'N/A'}) has been successfully cancelled.")
            return JsonResponse({'message': 'Payment cancelled successfully.'})

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON in request body.'}, status=400)
        except Exception as e:
            messages.error(request, f"Failed to cancel payment: {e}")
            return JsonResponse({'error': f'An error occurred: {e}'}, status=500)
    
    # If not a POST request, return Method Not Allowed
    return JsonResponse({'error': 'Method not allowed.'}, status=405)

