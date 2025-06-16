# apps/payment/views.py

from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse  # This is important for form action URLs
from django.contrib import messages
from django.views.generic import ListView
from django.db.models import Sum, Max, Q
from django.utils import timezone
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin

# Import your models from their respective app locations
from apps.individual.models import Individual
from apps.family.models import Family
from apps.church.models import Church
from .models import Payment, ContributionType
from .forms import PaymentForm


# --- Existing Class-Based Views (CBVs) - no change needed here ---
class PaymentListView(LoginRequiredMixin, ListView):
    model = Payment
    template_name = 'payment/payment_list.html'
    context_object_name = 'payment'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset().select_related(
            'individual', 'contribution_type').order_by('-date_paid', '-id')

        contribution_type_id = self.request.GET.get('contribution_type')
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')

        if contribution_type_id:
            queryset = queryset.filter(
                contribution_type_id=contribution_type_id)
        if start_date:
            queryset = queryset.filter(date_paid__gte=start_date)
        if end_date:
            queryset = queryset.filter(date_paid__lte=end_date)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['contribution_types'] = ContributionType.objects.all().order_by(
            'name')

        filtered_payments = self.get_queryset()
        context['total_amount'] = filtered_payments.aggregate(Sum('amount'))[
            'amount__sum'] or 0.00
        context['latest_payment'] = filtered_payments.order_by(
            '-date_paid', '-id').first()
        context['page_title'] = 'All Payments'
        return context


# --- API View for Contribution Type Details (No change needed) ---
@require_http_methods(["GET"])
@login_required
def contribution_type_detail_api(request, pk):
    try:
        contribution_type = get_object_or_404(ContributionType, pk=pk)
        data = {
            'id': contribution_type.id,
            'name': contribution_type.name,
            'amount': str(contribution_type.amount),
            'description': contribution_type.description,
        }
        return JsonResponse(data)
    except ContributionType.DoesNotExist:
        return JsonResponse({'error': 'ContributionType not found'}, status=404)
    except Exception as e:
        print(f"Error in contribution_type_detail_api: {e}")
        return JsonResponse({'error': str(e)}, status=500)


# --- NEW API VIEW: To fetch family details and members for JavaScript (No change needed) ---
@require_http_methods(["GET"])
@login_required
def get_individual_family_details_api(request, individual_id):
    individual = get_object_or_404(Individual, id=individual_id)

    family_name = "No Family Assigned"
    family_members_data = []
    family_id = None
    municipality = "N/A"
    barangay = "N/A"

    if individual.family:
        family = individual.family
        family_id = family.id

        family_head = Individual.objects.filter(
            family=family,
            relationship='HEAD',
            is_active_member=True,
            is_alive=True
        ).first()

        if family_head:
            family_name = f"FAMILY OF {family_head.full_name.upper()}"
        elif family.family_name:
            family_name = family.family_name.upper()
        else:
            family_name = "UNNAMED FAMILY"

        family_members = Individual.objects.filter(
            family=family,
            is_active_member=True,
            is_alive=True
        ).order_by('surname', 'given_name')

        for member in family_members:
            family_members_data.append({
                'id': member.id,
                'code': getattr(member, 'code', ''),
                'full_name': member.full_name,
                'membership_status': member.get_membership_status_display() if hasattr(member, 'get_membership_status_display') else '',
                'status': 'Alive' if member.is_alive else 'Deceased',
                'relationship': member.relationship
            })
    else:
        if individual.is_active_member and individual.is_alive:
            family_members_data.append({
                'id': individual.id,
                'code': getattr(individual, 'code', ''),
                'full_name': individual.full_name,
                'membership_status': individual.get_membership_status_display() if hasattr(individual, 'get_membership_status_display') else '',
                'status': 'Alive' if individual.is_alive else 'Deceased',
                'relationship': individual.relationship
            })
        family_name = f"{individual.full_name}'s Individual Payment"

        if hasattr(individual, 'address') and individual.address:
            # Assuming individual.address is a string field for municipality/barangay
            # If it's a related model, you'd access like individual.address.municipality
            # This part depends on how your Individual.address field is structured.
            # I'll keep the previous assumption that it might be a related model.
            municipality = individual.address.municipality if hasattr(
                individual.address, 'municipality') else 'N/A'
            barangay = individual.address.barangay if hasattr(
                individual.address, 'barangay') else 'N/A'

    all_active_individuals = Individual.objects.filter(
        is_active_member=True,
        is_alive=True
    ).order_by('surname', 'given_name')

    share_for_options = [{
        'id': ind.id,
        'full_name': ind.full_name
    } for ind in all_active_individuals]

    data = {
        'family_id': family_id,
        'family_name': family_name,
        'municipality': municipality,
        'barangay': barangay,
        'family_members': family_members_data,
        'share_for_options': share_for_options,
        'individual_full_name': individual.full_name,
    }

    return JsonResponse(data)


# --- MODIFIED: THE MAIN PAYMENT CREATION VIEW (Handles GET requests to display the full form) ---
# Now accepts individual_id from URL
# Removed @require_http_methods(["GET"]) because it's implicit for a view that gets a form
@login_required
# individual_id is now a URL parameter
def payment_create_full_form_view(request, individual_id=None):
    # 1. Prerequisite Checks (No change needed here for now, they are fine)
    if not Church.objects.exists():
        messages.info(
            request, "Walang Church record! Please add a Church first before creating payments.")
        if request.user.is_staff:
            add_church_url = reverse('admin:church_church_add')
            redirect_url = f"{add_church_url}?next={request.path}"
            return redirect(redirect_url)
        else:
            return render(request, 'payment/payment_error.html', {'message': 'Please contact an administrator to add Church details.'})

    if not Family.objects.exists():
        messages.info(
            request, "Walang Family record! Please add a Family first before creating payments.")
        if request.user.is_staff:
            add_family_url = reverse('admin:family_family_add')
            redirect_url = f"{add_family_url}?next={request.path}"
            return redirect(redirect_url)
        else:
            return render(request, 'payment/payment_error.html', {'message': 'Please contact an administrator to add Family details.'})

    if not Individual.objects.exists():
        messages.info(
            request, "Walang Individual record! Please add an Individual first before creating payments.")
        if request.user.is_staff:
            add_individual_url = reverse('admin:individual_individual_add')
            redirect_url = f"{add_individual_url}?next={request.path}"
            return redirect(redirect_url)
        else:
            return render(request, 'payment/payment_error.html', {'message': 'Please contact an administrator to add Individual details.'})

    if not ContributionType.objects.exists():
        messages.warning(
            request, "Walang Contribution Type record! You need at least one Contribution Type to create a payment.")
        if request.user.is_staff:
            add_contribution_type_url = reverse(
                'admin:payment_contributiontype_add')
            current_path = request.path
            redirect_url = f"{add_contribution_type_url}?next={current_path}"
            return redirect(redirect_url)
        else:
            messages.error(
                request, "Please contact an administrator to add Contribution Types before creating payments.")
            return render(request, 'payment/payment_error.html', {'message': 'Please contact an administrator to add Contribution Types.'})

    # Get the individual object if an ID is provided in the URL
    initial_payee = None
    if individual_id:
        try:
            selected_individual = Individual.objects.get(pk=individual_id)
            
            # If the selected individual belongs to a family, find the family head
            if selected_individual.family:
                family_head = Individual.objects.filter(
                    family=selected_individual.family,
                    relationship='HEAD',
                    is_active_member=True,
                    is_alive=True
                ).first()
                if family_head:
                    initial_payee = family_head
                else:
                    messages.warning(request, f"No family head found for the family of {selected_individual.full_name}. Payee field will not be pre-selected based on family head.")
            else:
                # If selected individual does not belong to a family,
                # only use them as initial payee if they themselves are a 'HEAD'.
                if selected_individual.relationship == 'HEAD' and \
                   selected_individual.is_active_member and \
                   selected_individual.is_alive:
                    initial_payee = selected_individual
                else:
                    messages.info(request, f"{selected_individual.full_name} is not a family head and does not belong to a family. Payee field will not be pre-selected.")

        except Individual.DoesNotExist:
            messages.error(request, "Selected individual not found.")
            # Redirect back to dashboard if individual doesn't exist
            return redirect('individual:individual_dashboard')

    # Initialize the form with initial individual if available
    form = PaymentForm(initial={'individual': initial_payee})

    context = {
        'form': form,
        'page_title': 'Add New Payment',
        'is_update_mode': False,
        'individual': initial_payee,  # Pass the actual payee to the template for display if needed
    }

    return render(request, 'payment/payment_form.html', context)


# --- THE MAIN PAYMENT ADDITION VIEW (Handles POST requests for form submission) ---
# This view should ONLY handle POST. The GET part is handled by payment_create_full_form_view
@require_http_methods(["POST"])
@login_required
def payment_create_view(request):
    form = PaymentForm(request.POST)

    if form.is_valid():
        payment = form.save(commit=False)
        payment.save()

        # Handle ManyToMany for covered_members if your Payment model has it
        selected_members_ids = request.POST.getlist('selected_members')
        if selected_members_ids:
            covered_individuals = Individual.objects.filter(
                id__in=selected_members_ids)
            # Make sure Payment model has covered_members ManyToManyField
            payment.covered_members.set(covered_individuals)
        else:
            payment.covered_members.clear()

        messages.success(
            request, f"Payment added successfully for {payment.individual.full_name}.")
        # Redirect to the payment list after successful creation
        return redirect('payment:payment_list')
    else:
        messages.error(
            request, "There was an error in your form submission. Please correct the errors.")

        # Re-render the form with errors, ensuring all context variables are available
        # This is crucial so the form template has everything it needs on error
        context = {
            'form': form,
            'page_title': 'Add New Payment - Error',
            'is_update_mode': False,
            # If the individual field was in the POST data, try to retrieve it for display
            'individual': form.cleaned_data.get('individual') if form.is_valid() else Individual.objects.filter(pk=request.POST.get('individual')).first(),
            # You might also need to pass other context related to family_details_api if the form relies on JS for that
        }
        return render(request, 'payment/payment_form.html', context)


# --- Payment Detail View (No change needed) ---
@login_required
def payment_detail_view(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    covered_members = payment.covered_members.all().order_by('surname', 'given_name')
    context = {
        'payment': payment,
        'covered_members': covered_members,
        'page_title': f'Payment Details - {payment.receipt_no}',
    }
    return render(request, 'payment/payment_detail.html', context)


# --- Payment Update View (No change needed) ---
@require_http_methods(["GET", "POST"])
@login_required
def payment_update_view(request, pk):
    payment = get_object_or_404(Payment, pk=pk)

    if request.method == 'POST':
        form = PaymentForm(request.POST, instance=payment)
        if form.is_valid():
            with transaction.atomic():
                form.save()

                selected_members_ids = request.POST.getlist(
                    'selected_members')
                if selected_members_ids:
                    covered_individuals = Individual.objects.filter(
                        id__in=selected_members_ids)
                    payment.covered_members.set(covered_individuals)
                else:
                    payment.covered_members.clear()

            messages.success(
                request, f"Payment {payment.receipt_no} updated successfully!")
            return redirect('payment:payment_detail', pk=payment.id)
        else:
            messages.error(
                request, "There was an error in your form submission. Please correct the errors.")
    else:
        form = PaymentForm(instance=payment)

    context = {
        'form': form,
        'payment': payment,
        'page_title': f'Edit Payment - {payment.receipt_no}',
        'is_update_mode': True
    }
    return render(request, 'payment/payment_form.html', context)


# --- Payment Delete View (No change needed) ---
@require_http_methods(["POST"])
@login_required
def payment_delete_view(request, pk):
    payment = get_object_or_404(Payment, pk=pk)

    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(
            request, "You don't have permission to delete payments.")
        return redirect('payment:payment_detail', pk=pk)

    individual_id = payment.individual.id
    payment.delete()
    messages.success(request, "Payment deleted successfully!")
    # Redirect to the individual dashboard instead of individual_detail, for smoother UX
    return redirect('individual:individual_dashboard')