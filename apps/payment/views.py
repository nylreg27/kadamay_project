# apps/payment/views.py

from django.shortcuts import render, redirect, get_object_or_404
# Added ListView and DetailView
from django.views.generic import View, CreateView, ListView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
# For permission checks
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
# For atomic transactions (saving multiple related objects)
from django.db import transaction
from django.http import JsonResponse
from django.db.models import Q  # For search queries

from .models import Payment, PaymentIndividualAllocation, ContributionType
# Import Individual and Family models
from apps.individual.models import Individual, Family
from apps.church.models import Church  # Import Church model
from .forms import PaymentForm, PaymentIndividualAllocationFormSet


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Max
from .models import Payment, Payee, Family, Individual
from .forms import PaymentForm, PaymentPayeeFormset


# Helper function to check user roles
def is_admin_or_cashier_or_incharge(user):
    """
    Checks if the user belongs to 'Admin', 'Cashier', or 'In-charge' groups.
    Assumes your user model has a 'groups' field.
    """
    if user.is_superuser:
        return True
    return user.groups.filter(name__in=['Admin', 'Cashier', 'In-charge']).exists()


class PaymentAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin to ensure only 'Admin', 'Cashier', or 'In-charge' users can access these views.
    """

    def test_func(self):
        return is_admin_or_cashier_or_incharge(self.request.user)

    def handle_no_permission(self):
        messages.error(
            self.request, "You do not have permission to access payment functions.")
        # Redirect to a home/dashboard page
        return redirect(reverse_lazy('home'))


class PaymentListView(PaymentAccessMixin, ListView):
    """
    Lists all Payment records.
    Accessible only by Admin, Cashier, In-charge.
    """
    model = Payment
    template_name = 'payment/payment_list.html'  # You'll create this next
    context_object_name = 'payments'
    paginate_by = 10

    def get_queryset(self):
        # Prefetch related data for efficiency
        queryset = Payment.objects.select_related(
            'individual',
            'church',
            'contribution_type',
            'created_by',
            'updated_by',
            'collected_by',
            'validated_by',
            'cancelled_by',
            'deceased_member'
            # Prefetch individuals in allocations
        ).prefetch_related('individual_allocations__individual')

        # Basic search functionality (e.g., by OR number, payer name)
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(receipt_number__icontains=search_query) |
                Q(individual__given_name__icontains=search_query) |
                Q(individual__surname__icontains=search_query) |
                Q(gcash_reference_number__icontains=search_query) |
                Q(notes__icontains=search_query)
            )

        # Filter by status if requested
        status_filter = self.request.GET.get('status')
        if status_filter and status_filter != 'ALL':
            queryset = queryset.filter(payment_status=status_filter)

        # Filter by payment method
        method_filter = self.request.GET.get('method')
        if method_filter and method_filter != 'ALL':
            queryset = queryset.filter(payment_method=method_filter)

        return queryset.order_by('-date_paid', '-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Payment Records'
        context['search_query'] = self.request.GET.get('search', '')
        context['current_status_filter'] = self.request.GET.get(
            'status', 'ALL')
        context['current_method_filter'] = self.request.GET.get(
            'method', 'ALL')
        context['payment_statuses'] = Payment.PAYMENT_STATUS_CHOICES
        context['payment_methods'] = Payment.PAYMENT_METHOD_CHOICES
        return context


class PaymentDetailView(PaymentAccessMixin, DetailView):
    """
    Displays details of a single Payment record.
    Accessible only by Admin, Cashier, In-charge.
    """
    model = Payment
    template_name = 'payment/payment_detail.html'  # You'll create this later
    context_object_name = 'payment'

    def get_queryset(self):
        # Prefetch all related data for the detail view
        return Payment.objects.select_related(
            'individual',
            'church',
            'contribution_type',
            'created_by',
            'updated_by',
            'collected_by',
            'validated_by',
            'cancelled_by',
            'deceased_member'
        ).prefetch_related('individual_allocations__individual')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Payment Details'
        return context


class AddPaymentView(PaymentAccessMixin, View):
    """
    Handles both displaying the payment form (GET) and processing its submission (POST).
    This view supports adding multiple allocations per payment.
    """
    template_name = 'payment/payment_form.html'  # The template we just created

    def get(self, request, individual_id=None):
        initial_data = {}
        if individual_id:
            individual = get_object_or_404(Individual, pk=individual_id)
            initial_data['individual'] = individual
            initial_data[
                'primary_individual_search'] = f"{individual.full_name} ({individual.membership_id})"

        form = PaymentForm(initial=initial_data)
        # Pass an empty queryset for individual in formset to be populated by Select2
        formset = PaymentIndividualAllocationFormSet(
            queryset=PaymentIndividualAllocation.objects.none()
        )

        context = {
            'form': form,
            'formset': formset,
            'page_title': 'Record New Payment',
            # Pass individual if present
            'individual': initial_data.get('individual')
        }
        return render(request, self.template_name, context)

    def post(self, request, individual_id=None):
        form = PaymentForm(request.POST)
        formset = PaymentIndividualAllocationFormSet(request.POST)

        if form.is_valid():
            # Check if an individual was actually selected from search
            primary_individual_id = request.POST.get('individual')
            if not primary_individual_id:
                messages.error(
                    request, "Please select a primary payer from the search results.")
                # Re-render form with errors
                context = {
                    'form': form,
                    'formset': formset,
                    'page_title': 'Record New Payment',
                    'individual': None  # No individual selected
                }
                return render(request, self.template_name, context)

            primary_individual = get_object_or_404(
                Individual, pk=primary_individual_id)
            # Assign the actual Individual object
            form.instance.individual = primary_individual

            # Set collected_by based on the current user
            if request.user.is_authenticated:
                form.instance.collected_by = request.user
                # For cash payments, if user is Admin/Cashier, it's validated immediately
                if form.instance.payment_method == 'CASH' and is_admin_or_cashier_or_incharge(request.user):
                    form.instance.payment_status = 'VALIDATED'
                    form.instance.validated_by = request.user
                    form.instance.validation_date = transaction.now()
                # For GCash payments, status is PENDING_VALIDATION if user is In-charge
                elif form.instance.payment_method == 'GCASH' and 'In-charge' in [g.name for g in request.user.groups.all()]:
                    form.instance.payment_status = 'PENDING_VALIDATION'
                # If Admin/Cashier making a GCash payment, it can be validated immediately too
                elif form.instance.payment_method == 'GCASH' and ('Admin' in [g.name for g in request.user.groups.all()] or 'Cashier' in [g.name for g in request.user.groups.all()]):
                    form.instance.payment_status = 'VALIDATED'
                    form.instance.validated_by = request.user
                    form.instance.validation_date = transaction.now()

            # Pass the request user to the form's instance for the save method's created_by/updated_by logic
            # This is a common pattern when you need to access request data in model's save method
            form.instance._request_user = request.user

            # Use a transaction to ensure all saves succeed or none do
            with transaction.atomic():
                payment = form.save()  # Save the main payment object first

                # Now handle the formset for individual allocations
                # Associate the formset with the saved payment instance
                formset = PaymentIndividualAllocationFormSet(
                    request.POST, instance=payment)

                # Check formset validity after attaching to instance
                if formset.is_valid():
                    # Process formset data from hidden input
                    # This is crucial because crispy forms' formset doesn't directly handle the dynamic additions
                    formset_data_json = request.POST.get('formset_data')
                    if formset_data_json:
                        import json
                        formset_data = json.loads(formset_data_json)

                        # Delete existing allocations not in the submitted data
                        existing_allocation_ids = [
                            alloc.id for alloc in payment.individual_allocations.all()]
                        submitted_individual_ids = [
                            item['individual_id'] for item in formset_data]

                        for alloc_id in existing_allocation_ids:
                            # If an allocation from the database is not in the submitted data, delete it.
                            # Or if it was explicitly marked for delete in the formset (though our JS hides it)
                            if str(alloc_id) not in [str(item['id']) for item in formset_data if 'id' in item]:
                                # This requires the formset_data to include the PK if it's an existing record.
                                # Let's simplify: Django formset will handle updates/deletes if 'id' field is sent.
                                # Our formset template doesn't explicitly send 'id' for existing, only for new.
                                # Instead, the DELETE checkbox handles it.
                                pass

                    # Save the formset
                    formset.save()  # This will create, update, or delete allocations based on the formset data

                    # After saving, check if any allocations were saved.
                    # If no allocations were made, but a primary individual was selected,
                    # make sure that primary individual is also allocated the full amount.
                    if not payment.individual_allocations.exists():
                        # Create an allocation for the primary individual with the full payment amount
                        PaymentIndividualAllocation.objects.create(
                            payment=payment,
                            individual=primary_individual,
                            allocated_amount=payment.amount,
                            is_payer=True
                        )
                        messages.warning(
                            request, "No specific allocations were made, so the full payment amount was allocated to the primary payer.")

                    messages.success(
                        request, f"Payment (OR: {payment.receipt_number}) recorded successfully!")
                    return redirect(reverse_lazy('payment:payment_detail', kwargs={'pk': payment.pk}))
                else:
                    messages.error(
                        request, "There were errors in the family member allocations. Please correct them.")
        else:
            messages.error(
                request, "There was an error with the main payment form. Please correct the highlighted fields.")

        # Re-render the form with errors
        context = {
            'form': form,
            'formset': formset,
            'page_title': 'Record New Payment',
            # Pass individual if present for re-render
            'individual': form.instance.individual
        }
        return render(request, self.template_name, context)


# --- API Views for JavaScript Interaction ---

def search_individuals_api(request):
    """
    API endpoint for Select2 to search individuals by name or membership ID.
    Returns a JSON response suitable for Select2.
    """
    query = request.GET.get('q', '')
    individual_id = request.GET.get('id', '')  # For pre-populating Select2

    individuals = Individual.objects.none()

    if query:
        individuals = Individual.objects.filter(
            Q(given_name__icontains=query) |
            Q(middle_name__icontains=query) |
            Q(surname__icontains=query) |
            Q(membership_id__icontains=query)
            # Limit results for performance
        ).order_by('surname', 'given_name')[:10]
    elif individual_id:
        try:
            individuals = Individual.objects.filter(pk=individual_id)
        except ValueError:
            pass  # Invalid ID, no results

    results = []
    for ind in individuals:
        results.append({
            'id': ind.pk,
            'text': ind.full_name,  # Select2 expects 'text' for display
            'membership_id': ind.membership_id,
            'family_name': ind.family.family_name if ind.family else 'N/A',
            'status': ind.membership_status  # Pass status for badges if needed
        })

    return JsonResponse({'items': results, 'total_count': individuals.count()})


def get_individual_family_details_api(request, pk):
    """
    API endpoint to get family details (including members) for a given individual.
    Used to populate the family members allocation formset.
    """
    individual = get_object_or_404(Individual, pk=pk)

    family_data = {
        'family_name': individual.family.family_name if individual.family else None,
        'family_members': []
    }

    if individual.family:
        for member in individual.family.members.all().order_by('surname', 'given_name'):
            family_data['family_members'].append({
                'id': member.pk,
                'full_name': member.full_name,
                'relationship': member.get_relationship_display_value(),
                'status': member.get_membership_status_display(),
                'is_payer_candidate': True  # All family members can potentially be payers
            })

    return JsonResponse(family_data)


def get_contribution_type_details_api(request, pk):
    """
    API endpoint to get details (specifically the amount) for a given contribution type.
    Used to auto-populate the per-member contribution amount.
    """
    contribution_type = get_object_or_404(ContributionType, pk=pk)
    data = {
        'id': contribution_type.pk,
        'name': contribution_type.name,
        # Convert Decimal to float for JSON serialization
        'amount': float(contribution_type.amount)
    }
    return JsonResponse(data)


@login_required
def payment_list(request):
    # This view will now handle both all payments and pending payments
    status_filter = request.GET.get('status')

    if status_filter == 'PENDING_VALIDATION':
        payments = Payment.objects.filter(
            payment_status='PENDING_VALIDATION').order_by('-or_number')
        title = "Pending Payments for Validation"
    else:
        payments = Payment.objects.all().order_by('-or_number')
        title = "All Payments"

    context = {
        'payments': payments,
        'title': title
    }
    return render(request, 'payment/payment_list.html', context)


@login_required
def create_payment(request):
    if not (request.user.is_superuser or request.user.is_cashier or request.user.is_incharge):
        messages.error(
            request, "You do not have permission to create payments.")
        # or any other appropriate redirect
        return redirect('payment:payment_list')

    # Automatic OR number generation
    # Get the maximum OR number and increment it
    last_or_number = Payment.objects.all().aggregate(
        Max('or_number'))['or_number__max']
    if last_or_number:
        try:
            # Assuming OR numbers are numeric and incrementable, e.g., '2000134'
            next_or_number = str(int(last_or_number) + 1)
        except ValueError:
            # Handle cases where OR number might not be purely numeric (e.g., 'OR-XYZ')
            # For simplicity, if non-numeric, we'll start from a default or require manual input
            messages.warning(
                request, "Automatic OR number generation failed for non-numeric OR. Please enter manually.")
            next_or_number = None  # Or '1000001' or similar starting point
    else:
        next_or_number = '2000001'  # Starting OR number if no payments exist

    if request.method == 'POST':
        form = PaymentForm(request.POST, user=request.user)
        formset = PaymentPayeeFormset(request.POST, prefix='payees')

        if form.is_valid() and formset.is_valid():
            payment = form.save(commit=False)
            payment.recorded_by = request.user

            # If OR number is not provided in the form (e.g., if hidden and auto-generated)
            # or if the form allows override but we want to stick to auto-gen on creation
            if not payment.or_number:
                payment.or_number = next_or_number

            # Payment Status logic
            if payment.payment_method == 'GCASH' and request.user.is_incharge:
                payment.payment_status = 'PENDING_VALIDATION'
            else:
                # Cash payments or Gcash by admin/cashier are immediately paid
                payment.payment_status = 'PAID'

            payment.save()

            payees = formset.save(commit=False)
            for payee in payees:
                payee.payment = payment
                payee.save()

                # Update individual's account
                individual = payee.individual
                # Assuming this field exists or logic is handled
                individual.current_balance += payment.amount_paid_by_payee_for_this_payment
                individual.save()

            messages.success(
                request, f"Payment {payment.or_number} created successfully!")
            return redirect('payment:payment_list')
        else:
            messages.error(
                request, "There was an error creating the payment. Please check your inputs.")
    else:
        form = PaymentForm(
            initial={'or_number': next_or_number}, user=request.user)
        # Empty formset for new entry
        formset = PaymentPayeeFormset(
            prefix='payees', queryset=Payee.objects.none())

    context = {
        'form': form,
        'formset': formset,
        'title': 'Create New Payment',
        'next_or_number': next_or_number,  # Pass this to display if needed
    }
    return render(request, 'payment/create_payment.html', context)

# Add other payment views here (e.g., payment_detail, validate_payment)
