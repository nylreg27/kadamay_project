# apps/payment/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.http import JsonResponse
import json
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db.models import Sum # Import Sum for total allocated amount calculation

from .forms import PaymentForm, PaymentIndividualAllocationFormSet # Import the formset!
from .models import Payment, Individual, ContributionType, PaymentIndividualAllocation # Import necessary models
from apps.family.models import Family # Need to import Family for get_family_details_api_view

# Helper function to check if user is an admin or cashier
# For Kadamay_project, let's define cashiers via a group.
# Ensure you create a Django group named 'Cashiers' and add relevant users to it.
def is_admin_or_cashier(user):
    return user.is_superuser or user.groups.filter(name='Cashiers').exists()

# Function-based view for payment creation
@login_required
@user_passes_test(is_admin_or_cashier, login_url='/accounts/login/?next=/payment/all/') # Restrict access
def payment_create_full_form_view(request, individual_id=None):
    individual = None
    if individual_id:
        individual = get_object_or_404(Individual, pk=individual_id)

    if request.method == 'POST':
        # Pass instance=None for new Payment, or an existing instance for editing
        form = PaymentForm(request.POST, instance=None)
        # Pass prefix to formset to avoid conflicts if multiple formsets are used
        formset = PaymentIndividualAllocationFormSet(request.POST, instance=None, prefix='allocations')

        if form.is_valid() and formset.is_valid():
            with transaction.atomic(): # Ensure atomicity for saving Payment and its allocations
                payment = form.save(commit=False)
                # Attach the current user to the payment being created/updated
                payment._request_user = request.user
                payment.created_by = request.user
                payment.payment_status = 'PENDING_VALIDATION' # New payments start as PENDING_VALIDATION
                payment.save()

                # Associate each allocation form with the newly saved payment
                # Save the formset, committing to the database
                formset.instance = payment # Link the formset to the saved payment instance
                allocations = formset.save(commit=False)
                
                total_allocated = sum(alloc.allocated_amount for alloc in allocations if not alloc.DELETE)
                if total_allocated != payment.amount:
                    messages.error(request, f"Error: Total allocated amount (₱{total_allocated:.2f}) does not match total payment amount (₱{payment.amount:.2f}). Please adjust allocations.")
                    # Manually mark formset as invalid to re-render with errors
                    formset._errors = [{} for _ in range(len(formset.forms))]
                    for i, alloc_form in enumerate(formset.forms):
                        if alloc_form.cleaned_data and not alloc_form.cleaned_data.get('DELETE'):
                            if alloc_form.cleaned_data.get('allocated_amount') is None: # Catch if field is cleared
                                alloc_form.add_error('allocated_amount', 'Amount required.')

                    # Re-render the form with errors
                    context = {
                        'form': form,
                        'formset': formset,
                        'page_title': 'Add New Payment'
                    }
                    if individual:
                        context['individual'] = individual
                        context['page_title'] = f'Add Payment for {individual.full_name}'
                    return render(request, 'payment/payment_form.html', context)
                
                # If amounts match, save all allocations
                for alloc in allocations:
                    if not alloc.DELETE: # Only save if not marked for deletion
                        alloc.save()
                
                # Handle deletions from the formset
                formset.save_m2m() # For any ManyToMany if applicable, though not used here directly

            messages.success(request, f"Payment for {payment.individual.full_name} (OR: {payment.receipt_number}) added successfully and is now PENDING VALIDATION!")
            return redirect(payment.get_absolute_url()) # Redirect to the detail page

        else: # If form or formset is not valid
            messages.error(request, "Please correct the errors below.")
            
    else: # GET request
        form = PaymentForm(initial={'individual': individual} if individual else None)
        formset = PaymentIndividualAllocationFormSet(instance=None, prefix='allocations') # Initialize empty formset

    context = {
        'form': form,
        'formset': formset,
        'page_title': 'Add New Payment',
    }
    if individual:
        context['individual'] = individual
        context['page_title'] = f'Add Payment for {individual.full_name}'

    return render(request, 'payment/payment_form.html', context)


@login_required
def payment_list_view(request):
    payments = Payment.objects.all().order_by('-date_paid', '-created_at')
    # Add filtering for non-admin/cashier users if needed (e.g., only show their own payments)
    if not is_admin_or_cashier(request.user):
        payments = payments.filter(created_by=request.user)

    context = {
        'payments': payments,
        'page_title': 'All Payments',
        'is_admin_or_cashier': is_admin_or_cashier(request.user) # Pass this to template
    }
    return render(request, 'payment/payment_list.html', context)


@login_required
def payment_detail_view(request, pk):
    payment = get_object_or_404(Payment, pk=pk)

    # For non-admin/cashier, only allow viewing if they created it
    if not is_admin_or_cashier(request.user) and payment.created_by != request.user:
        messages.error(request, "You do not have permission to view this payment.")
        return redirect(reverse('payment:payment_list')) # Redirect to their own list or dashboard

    # Get all individual allocations for this payment
    allocations = payment.individual_allocations.all().order_by('individual__surname')

    context = {
        'payment': payment,
        'allocations': allocations, # Pass allocations to the template
        'page_title': f'Payment Details - OR: {payment.receipt_number or payment.pk}',
        'is_admin_or_cashier': is_admin_or_cashier(request.user) # Pass this to template
    }
    return render(request, 'payment/payment_detail.html', context)


@login_required
@user_passes_test(is_admin_or_cashier, login_url='/accounts/login/?next=/payment/all/') # Only admins/cashiers can cancel
def cancel_payment_view(request, pk):
    payment = get_object_or_404(Payment, pk=pk)

    if request.method == 'POST':
        cancellation_reason = request.POST.get('cancellation_reason', '').strip()
        if not cancellation_reason:
            messages.error(request, "Cancellation reason is required.")
            return redirect(reverse('payment:payment_detail', kwargs={'pk': pk}))

        if payment.payment_status == 'CANCELLED':
            messages.info(request, "This payment is already cancelled.")
            return redirect(reverse('payment:payment_detail', kwargs={'pk': pk}))

        try:
            with transaction.atomic():
                payment._request_user = request.user # Attach user for model's save method
                payment.is_cancelled = True
                payment.cancellation_reason = cancellation_reason
                payment.payment_status = 'CANCELLED' # Explicitly set status to CANCELLED
                payment.save(update_fields=['is_cancelled', 'cancellation_reason', 'payment_status', 'cancelled_by', 'cancellation_date', 'updated_at'])

            messages.success(request, f"Payment (OR: {payment.receipt_number or 'N/A'}) has been successfully cancelled.")
            return redirect(reverse('payment:payment_detail', kwargs={'pk': pk}))
        except Exception as e:
            messages.error(request, f"Error cancelling payment: {e}")
            return redirect(reverse('payment:payment_detail', kwargs={'pk': pk}))

    context = {
        'payment': payment,
        'page_title': f'Cancel Payment - OR: {payment.receipt_number or payment.pk}'
    }
    return render(request, 'payment/cancel_payment_confirm.html', context) # You'll need this template

@login_required
@user_passes_test(is_admin_or_cashier, login_url='/accounts/login/?next=/payment/admin/pending/') # Only admins/cashiers can validate
def pending_payments_list_view(request):
    pending_payments = Payment.objects.filter(payment_status='PENDING_VALIDATION').order_by('date_paid', 'created_at')
    context = {
        'pending_payments': pending_payments,
        'page_title': 'Payments Pending Validation',
        'is_admin_or_cashier': is_admin_or_cashier(request.user) # Pass this to template
    }
    return render(request, 'payment/pending_payments_list.html', context)


# === NEW: API endpoint to validate a payment ===
@require_http_methods(["POST"])
@login_required
@user_passes_test(is_admin_or_cashier) # Only admins/cashiers can perform validation
def validate_payment_view(request, pk):
    try:
        payment = get_object_or_404(Payment, pk=pk)

        # Check if the payment is actually pending validation
        if payment.payment_status != 'PENDING_VALIDATION':
            return JsonResponse({'error': 'Payment is not in pending validation status or has already been processed.'}, status=400)
        
        if payment.is_cancelled:
            return JsonResponse({'error': 'Cannot validate a cancelled payment.'}, status=400)


        with transaction.atomic():
            payment._request_user = request.user # Attach user for model's save method
            payment.payment_status = 'VALIDATED'
            # validated_by and validation_date are set in model's save method via _request_user
            payment.save(update_fields=['payment_status', 'validated_by', 'validation_date', 'updated_at']) # Save updated_at too

        messages.success(request, f"Payment (OR: {payment.receipt_number or 'N/A'}) has been successfully validated.")
        return JsonResponse({'message': 'Payment validated successfully.'})

    except Payment.DoesNotExist:
        return JsonResponse({'error': 'Payment not found.'}, status=404)
    except Exception as e:
        messages.error(request, f"An error occurred: {e}") # Display generic error
        return JsonResponse({'error': f'An unexpected error occurred: {e}'}, status=500)


# API to get family details for dynamic payee selection
@require_http_methods(["GET"])
@login_required
def get_family_details_api_view(request, individual_id):
    try:
        individual = get_object_or_404(Individual, pk=individual_id)
        if individual.relationship != 'HEAD':
            return JsonResponse({'error': 'Selected individual is not a head of family.'}, status=400)

        family = individual.family
        if not family:
            return JsonResponse({'error': 'Individual not associated with a family.'}, status=404)

        # Get all active and alive members of this family, excluding the payee
        family_members = Individual.objects.filter(
            family=family,
            is_active_member=True,
            is_alive=True
        ).exclude(pk=individual_id).order_by('surname', 'given_name')

        members_data = []
        for member in family_members:
            members_data.append({
                'id': member.id,
                'full_name': member.full_name,
                'membership_id': member.membership_id,
            })

        data = {
            'family_name': family.family_name,
            'church_name': family.church.name if family.church else 'N/A',
            'family_members': members_data
        }
        return JsonResponse(data)
    except Individual.DoesNotExist:
        return JsonResponse({'error': 'Individual not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# API to get contribution amount
@require_http_methods(["GET"])
@login_required
def get_contribution_amount_api_view(request, pk):
    try:
        contribution_type = get_object_or_404(ContributionType, pk=pk)
        return JsonResponse({'amount': str(contribution_type.amount)}) # Convert Decimal to string
    except ContributionType.DoesNotExist:
        return JsonResponse({'error': 'Contribution type not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)