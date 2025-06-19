# apps/payment/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import View, ListView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import transaction
from django.http import JsonResponse
from django.db.models import Q, Max # For search queries and Max for OR number

from apps.payment.models import Payment, ContributionType, CoveredMember # ADD CoveredMember here!
from apps.individual.models import Individual
from apps.church.models import Church
# Import the correct formset name, which is PayeeFormSet from forms.py
# based on our previous discussions, this should now be for CoveredMember
from .forms import PaymentForm, PayeeFormSet # This PayeeFormSet should be for CoveredMember

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
        return redirect(reverse_lazy('home')) # Assuming 'home' is your dashboard URL name


class PaymentListView(PaymentAccessMixin, ListView):
    """
    Lists all Payment records.
    Accessible only by Admin, Cashier, In-charge.
    """
    model = Payment
    template_name = 'payment/payment_list.html'
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
        ).prefetch_related('covered_members__individual') # Corrected: Use 'covered_members'

        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(receipt_number__icontains=search_query) |
                Q(individual__given_name__icontains=search_query) |
                Q(individual__surname__icontains=search_query) |
                Q(gcash_reference_number__icontains=search_query) |
                Q(notes__icontains=search_query)
            )

        status_filter = self.request.GET.get('status')
        if status_filter and status_filter != 'ALL':
            queryset = queryset.filter(payment_status=status_filter)

        method_filter = self.request.GET.get('method')
        if method_filter and method_filter != 'ALL':
            queryset = queryset.filter(payment_method=method_filter)

        return queryset.order_by('-date_paid', '-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Payment Records'
        context['search_query'] = self.request.GET.get('search', '')
        context['current_status_filter'] = self.request.GET.get('status', 'ALL')
        context['current_method_filter'] = self.request.GET.get('method', 'ALL')
        context['payment_statuses'] = Payment.PAYMENT_STATUS_CHOICES
        context['payment_methods'] = Payment.PAYMENT_METHOD_CHOICES
        return context


class PaymentDetailView(PaymentAccessMixin, DetailView):
    """
    Displays details of a single Payment record.
    Accessible only by Admin, Cashier, In-charge.
    """
    model = Payment
    template_name = 'payment/payment_detail.html'
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
        ).prefetch_related('covered_members__individual') # Corrected: Use 'covered_members'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Payment Details'
        return context


class AddPaymentView(PaymentAccessMixin, View):
    """
    Handles both displaying the payment form (GET) and processing its submission (POST).
    This view supports adding multiple allocations per payment.
    """
    template_name = 'payment/payment_form.html'

    def get(self, request, individual_id=None):
        initial_data = {}
        if individual_id:
            individual = get_object_or_404(Individual, pk=individual_id)
            initial_data['individual'] = individual.pk # Pass PK for the form field
            initial_data['primary_individual_search'] = f"{individual.full_name} ({individual.membership_id})"
        
        # Automatic OR number generation (same logic as the removed create_payment function)
        last_receipt = Payment.objects.all().aggregate(Max('receipt_number'))['receipt_number__max']
        if last_receipt:
            try:
                # Ensure it's treated as a numeric string for incrementing
                next_receipt_number = str(int(last_receipt) + 1)
            except (ValueError, TypeError):
                messages.warning(request, "Automatic Receipt Number generation failed. Please enter manually.")
                next_receipt_number = None # Or '2000001' or similar starting point
        else:
            next_receipt_number = '2000001' # Starting OR number if no payments exist
        
        initial_data['receipt_number'] = next_receipt_number # Set as initial value for the form

        form = PaymentForm(initial=initial_data)
        # Pass an empty queryset for formset, it will be populated by JS/Select2 for CoveredMembers
        formset = PayeeFormSet(
            queryset=CoveredMember.objects.none() # Corrected: Use CoveredMember
        )

        context = {
            'form': form,
            'formset': formset,
            'page_title': 'Record New Payment',
            'next_receipt_number': next_receipt_number, # Also pass to context for display if needed
            'individual': initial_data.get('individual') # Pass individual PK if present
        }
        return render(request, self.template_name, context)

    def post(self, request, individual_id=None):
        form = PaymentForm(request.POST)
        formset = PayeeFormSet(request.POST) # Still named PayeeFormSet but manages CoveredMember

        if form.is_valid():
            primary_individual_id = request.POST.get('individual')
            if not primary_individual_id:
                messages.error(
                    request, "Please select a primary payer from the search results.")
                context = {
                    'form': form,
                    'formset': formset,
                    'page_title': 'Record New Payment',
                    'individual': None
                }
                return render(request, self.template_name, context)

            primary_individual = get_object_or_404(Individual, pk=primary_individual_id)
            form.instance.individual = primary_individual

            if request.user.is_authenticated:
                form.instance.collected_by = request.user
                
                # Payment Status logic based on user roles and payment method
                # This needs to be 'PENDING_VALIDATION' only for In-charge + GCash
                # Admin/Cashier + GCash, and all CASH payments are 'PAID'
                if form.instance.payment_method == 'GCASH' and 'In-charge' in [g.name for g in request.user.groups.all()]:
                    form.instance.payment_status = 'PENDING_VALIDATION'
                else: # CASH payments by anyone, or GCash by Admin/Cashier
                    form.instance.payment_status = 'PAID'
                    form.instance.validated_by = request.user # Validated by collector if not pending
                    form.instance.validation_date = transaction.now()

            # The _request_user attribute is a pattern for model's save method to access current user
            form.instance._request_user = request.user

            with transaction.atomic():
                payment = form.save()

                # Now, correctly handle the formset for CoveredMember allocations
                formset_for_save = PayeeFormSet(request.POST, instance=payment)
                
                if formset_for_save.is_valid():
                    # Save the formset (creates, updates, deletes CoveredMember instances)
                    saved_covered_members = formset_for_save.save(commit=False)
                    for cm in saved_covered_members:
                        # You may need to explicitly set 'payment' for new objects if not handled by formset's save
                        # For new objects, base_form should link to payment, but explicit set is safer.
                        cm.payment = payment 
                        cm.save()
                    
                    # Handle deleted members (formset.save() with commit=False doesn't delete, needs extra step)
                    for obj in formset_for_save.deleted_objects:
                        obj.delete()

                    # After saving, check if any allocations were saved.
                    # If no specific allocations, allocate full amount to primary individual.
                    if not payment.covered_members.exists(): # Corrected: Use covered_members
                        # Check if primary_individual is already a CoveredMember for this payment (unlikely if .exists() is false)
                        # To avoid duplicates if somehow the primary individual was added manually without the formset.
                        CoveredMember.objects.create( # Corrected: Use CoveredMember
                            payment=payment,
                            individual=primary_individual,
                            amount_allocated=payment.amount,
                            # is_payer is not a field on CoveredMember, it's a property on Payment.
                            # So no need to set is_payer here for CoveredMember.
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
            'individual': form.instance.individual if form.instance.individual else None,
            'next_receipt_number': request.POST.get('receipt_number', 'N/A') # Re-populate if it was an auto-gen
        }
        return render(request, self.template_name, context)

# --- API Views for JavaScript Interaction (no changes needed for these if they work as intended) ---

def search_individuals_api(request):
    """
    API endpoint for Select2 to search individuals by name or membership ID.
    Returns a JSON response suitable for Select2.
    """
    query = request.GET.get('q', '')
    individual_id = request.GET.get('id', '') 

    individuals = Individual.objects.none()

    if query:
        individuals = Individual.objects.filter(
            Q(given_name__icontains=query) |
            Q(middle_name__icontains=query) |
            Q(surname__icontains=query) |
            Q(membership_id__icontains=query)
        ).order_by('surname', 'given_name')[:10]
    elif individual_id:
        try:
            individuals = Individual.objects.filter(pk=individual_id)
        except ValueError:
            pass 

    results = []
    for ind in individuals:
        results.append({
            'id': ind.pk,
            'text': ind.full_name,
            'membership_id': ind.membership_id,
            'family_name': ind.family.family_name if ind.family else 'N/A',
            'status': ind.membership_status
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
                'is_payer_candidate': True
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
        'amount': float(contribution_type.amount) # Convert Decimal to float for JSON
    }
    return JsonResponse(data)

