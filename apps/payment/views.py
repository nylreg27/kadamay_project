# apps/payment/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db import transaction  # Para sa atomic operations
# Para sa access control
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages  # Para sa user feedback
# Para sa date/time stamps (e.g., validated_at)
from django.utils import timezone

# Para sa Django Groups based roles (RECOMMENDED)
from django.contrib.auth.models import Group
from django.http import JsonResponse  # Para sa API views
# Para sa complex queries (e.g., OR conditions sa search)
from django.db.models import Q

# Import ang Payment at CoveredMember models (KEEP THESE HERE, these are local to payment app)
from .models import Payment, CoveredMember
# Import ang PaymentForm at CoveredMemberFormSet (KEEP THESE HERE, these are local to payment app)
from .forms import CoveredMemberFormSet, PaymentForm


# --- Helper Function: OR Number Generation ---


def generate_or_number():
    """
    Generates the next available Official Receipt (OR) number.
    Follows the highest existing OR number in the record.
    Ex: If the highest is 2000134, the next is 2000135.
    """
    last_payment = Payment.objects.order_by('-or_number').first()
    if last_payment and last_payment.or_number and last_payment.or_number.isdigit():
        # Convert to int, increment, then convert back to string
        next_or_number = str(int(last_payment.or_number) + 1)
    else:
        # Default starting OR number if no payments exist or if OR is not purely numeric
        next_or_number = "2000001"
    return next_or_number


# --- Custom Mixin for KADAMAY Role-Based Access Control ---
class KadamayRoleRequiredMixin(UserPassesTestMixin):
    """
    Custom mixin to check for specific KADAMAY roles based on Django Groups.
    This is the most flexible way to manage "Admin", "Cashier", "In-Charge" roles.
    """
    required_roles = [
    ]  # List of role names (strings) allowed to access the view

    def test_func(self):
        user = self.request.user

        # User must be logged in to proceed with any role check
        if not user.is_authenticated:
            return False

        # Superusers (Django Admin) always have access to everything
        if user.is_superuser:
            return True

        # Check if the user belongs to any of the required Django Groups
        # Get names of groups the user belongs to
        user_groups = user.groups.values_list('name', flat=True)
        for role_name in self.required_roles:
            if role_name in user_groups:
                return True

        # If the user is not a superuser and doesn't belong to any of the required groups
        return False

    def handle_no_permission(self):
        messages.warning(
            self.request, "You do not have the necessary permissions to access this page.")
        return redirect('login')  # Redirect to login page if no permission


# --- Payment List View ---
class PaymentListView(LoginRequiredMixin, ListView):
    """
    Displays a list of all payments.
    Optimized with select_related and prefetch_related for efficient database queries.
    """
    model = Payment
    template_name = 'payment/payment_list.html'  # Siguraduhin na tamang path ito
    context_object_name = 'payments'
    paginate_by = 15  # Example: 15 payments per page

    def get_queryset(self):
        # MOVE Individual IMPORT HERE if filtering by individual is enabled and causing circular import
        # from apps.individual.models import Individual # Temporary import if needed for filters here

        queryset = super().get_queryset()

        # Use select_related for ForeignKey relationships (one-to-one or many-to-one)
        # This fetches related objects in the same query, reducing database hits.
        queryset = queryset.select_related(
            'individual',        # The payer (ForeignKey to Individual)
            'individual__church',  # <--- CORRECTED: Access church through individual
            # Type of contribution (ForeignKey to ContributionType)
            'contribution_type',
            'collected_by',      # User who collected (ForeignKey to User)
            'validated_by',      # User who validated (ForeignKey to User)
            'cancelled_by',      # User who cancelled (ForeignKey to User)
        )
        # Use prefetch_related for ManyToMany relationships or reverse ForeignKeys
        # (like 'covered_members' which links back from CoveredMember to Payment)
        # This fetches related objects in separate queries but efficiently, preventing N+1 problems.
        queryset = queryset.prefetch_related(
            'covered_members',  # The related CoveredMember objects for each Payment
            'covered_members__individual'  # The Individual objects linked by CoveredMember
        )

        # --- Filtering Logic (Optional but good practice) ---
        or_number_filter = self.request.GET.get('or_number_filter')
        payer_filter = self.request.GET.get('payer_filter')
        status_filter = self.request.GET.get('status_filter')
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')

        if payer_filter:
            # THIS IS WHERE Individual model might be needed.
            # If `apps.individual.models` causes circular import when imported at top-level,
            # uncomment this temporary import:
            # from apps.individual.models import Individual # TEMPORARY: Import Individual here if needed for filter
            queryset = queryset.filter(
                Q(individual__first_name__icontains=payer_filter) |
                Q(individual__last_name__icontains=payer_filter)
            )

        # ... (other filters) ...

        if or_number_filter:
            queryset = queryset.filter(or_number__icontains=or_number_filter)
        if status_filter and status_filter != 'all':
            queryset = queryset.filter(status=status_filter)
        if start_date:
            queryset = queryset.filter(date_paid__gte=start_date)
        if end_date:
            queryset = queryset.filter(date_paid__lte=end_date)

        # Order the queryset (e.g., newest payments first, then by OR number)
        queryset = queryset.order_by('-date_paid', '-or_number')

        return queryset

# --- Payment Detail View ---


class PaymentDetailView(LoginRequiredMixin, DetailView):
    """
    Displays the details of a single payment.
    Includes related covered members using prefetch_related for efficiency.
    """
    model = Payment
    template_name = 'payment/payment_detail.html'  # Siguraduhin na tamang path ito
    context_object_name = 'payment'

    def get_queryset(self):
        # Same select_related and prefetch_related for detail view optimization
        queryset = super().get_queryset().select_related(
            # <--- CORRECTED: Access church through individual
            'individual', 'individual__church', 'contribution_type',
            'collected_by', 'validated_by', 'cancelled_by',
        ).prefetch_related(
            'covered_members',
            'covered_members__individual'
        )
        return queryset

# --- Payment Create View ---


class PaymentCreateView(LoginRequiredMixin, KadamayRoleRequiredMixin, CreateView):
    """
    Handles the creation of a new payment.
    Only users with 'Admin', 'Cashier', or 'In-Charge' roles can access.
    Uses a formset for multiple covered members and automatically generates OR number.
    """
    model = Payment
    form_class = PaymentForm
    template_name = 'payment/payment_form.html'  # Re-use the form template
    # Redirect to list after success
    success_url = reverse_lazy('payment:payment_list')
    # Define roles allowed to create payments
    required_roles = ['Admin', 'Cashier', 'In-Charge']

    def get_context_data(self, **kwargs):
        # MOVE UserChurch, Profile, Individual IMPORTS HERE IF NEEDED FOR FORM FIELDS/CHOICES
        # from apps.account.models import UserChurch, Profile # TEMPORARY: Import if needed
        # from apps.individual.models import Individual # TEMPORARY: Import if needed

        context = super().get_context_data(**kwargs)
        if self.request.POST:
            # If the form was submitted, use submitted data for formset
            context['covered_member_formset'] = CoveredMemberFormSet(
                self.request.POST, instance=self.object)
        else:
            # Otherwise, create an empty formset for new entry
            context['covered_member_formset'] = CoveredMemberFormSet(
                instance=self.object)

        # Pass the next generated OR number to the template/form
        context['next_or_number'] = generate_or_number()
        return context

    def form_valid(self, form):
        # Set OR number, creator, and collector before saving the Payment instance
        form.instance.or_number = generate_or_number()
        form.instance.created_by = self.request.user
        # The logged-in user collects the payment
        form.instance.collected_by = self.request.user

        # Determine initial payment status based on method (e.g., Gcash needs validation)
        # Assuming your PaymentForm has a 'payment_method' field (e.g., 'cash', 'gcash')
        payment_method = form.cleaned_data.get('payment_method')
        if payment_method == 'gcash':
            form.instance.status = 'pending'  # Gcash payments often require validation
        else:  # Default for cash or other direct payments
            form.instance.status = 'paid'

        context = self.get_context_data()
        covered_member_formset = context['covered_member_formset']

        # Ensures that either both Payment and CoveredMembers are saved, or none are.
        with transaction.atomic():
            self.object = form.save()  # Save the payment instance first

            if covered_member_formset.is_valid():
                # Link the formset to the newly created payment object and save all covered members
                covered_member_formset.instance = self.object
                covered_member_formset.save()
                messages.success(
                    self.request, f"Payment {self.object.or_number} and covered members saved successfully!")
                return super().form_valid(form)
            else:
                # If formset is invalid, add an error message and re-render the form
                messages.error(
                    self.request, "There were errors with the covered members. Please correct them.")
                # This will re-render the form with errors
                return self.form_invalid(form)

    def form_invalid(self, form):
        messages.error(
            self.request, "There were errors in the payment form. Please correct them.")
        # Make sure to pass formset errors as well if formset is involved
        context = self.get_context_data()
        # The formset is already in context from get_context_data if request.POST
        return render(self.request, self.template_name, context)


# --- Payment Update View ---
class PaymentUpdateView(LoginRequiredMixin, KadamayRoleRequiredMixin, UpdateView):
    """
    Handles updating an existing payment.
    Only users with 'Admin', 'Cashier', or 'In-Charge' roles can access.
    """
    model = Payment
    form_class = PaymentForm
    template_name = 'payment/payment_form.html'
    context_object_name = 'payment'
    success_url = reverse_lazy('payment:payment_list')
    # Define roles allowed to update payments
    required_roles = ['Admin', 'Cashier', 'In-Charge']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['covered_member_formset'] = CoveredMemberFormSet(
                self.request.POST, instance=self.object)
        else:
            context['covered_member_formset'] = CoveredMemberFormSet(
                instance=self.object)
        return context

    def form_valid(self, form):
        form.instance.updated_by = self.request.user  # Record who updated it
        context = self.get_context_data()
        covered_member_formset = context['covered_member_formset']

        with transaction.atomic():
            self.object = form.save()  # Save the updated payment

            if covered_member_formset.is_valid():
                covered_member_formset.instance = self.object  # Link formset to the payment
                covered_member_formset.save()  # This handles creating, updating, deleting members
                messages.success(
                    self.request, f"Payment {self.object.or_number} and covered members updated successfully!")
                return super().form_valid(form)
            else:
                messages.error(
                    self.request, "There were errors with the covered members. Please correct them.")
                return self.form_invalid(form)

    def form_invalid(self, form):
        messages.error(
            self.request, "There were errors in the payment form. Please correct them.")
        context = self.get_context_data()
        return render(self.request, self.template_name, context)


# --- Payment Delete View ---
class PaymentDeleteView(LoginRequiredMixin, KadamayRoleRequiredMixin, DeleteView):
    """
    Handles deleting a payment.
    Only users with 'Admin' role can access this (for security reasons).
    """
    model = Payment
    # You need to create this template
    template_name = 'payment/payment_confirm_delete.html'
    context_object_name = 'payment'
    success_url = reverse_lazy('payment:payment_list')
    required_roles = ['Admin']  # Only Admin can permanently delete payments

    def form_valid(self, form):
        # You might want to soft-delete payments (e.g., set an `is_cancelled` flag)
        # instead of hard deletion for auditing purposes. For now, it's hard delete.
        messages.success(
            self.request, f"Payment {self.get_object().or_number} deleted successfully!")
        return super().form_valid(form)


# --- Payment Status Update Views (for Gcash validation / cancellation) ---

class PaymentValidateView(LoginRequiredMixin, KadamayRoleRequiredMixin, UpdateView):
    """
    View for 'In-Charge' or 'Admin' to validate Gcash payments using a reference number.
    This changes the status from 'pending' to 'paid'.
    """
    model = Payment
    # Only allow these fields for update in this specific form/view
    # Make sure gcash_reference_number is in your Payment model
    fields = ['status', 'gcash_reference_number']
    # Create a simple validation form
    template_name = 'payment/payment_validate_form.html'
    success_url = reverse_lazy('payment:payment_list')
    required_roles = ['Admin', 'In-Charge']  # Only these roles can validate

    def form_valid(self, form):
        payment = form.instance
        # Check if the payment is 'pending' and its method is 'gcash' before validating
        if payment.status == 'pending' and payment.payment_method == 'gcash':
            payment.status = 'paid'  # Change status to paid
            payment.validated_by = self.request.user
            payment.validated_at = timezone.now()  # Record validation timestamp
            messages.success(
                self.request, f"Gcash Payment {payment.or_number} validated successfully!")
            return super().form_valid(form)
        else:
            messages.error(
                self.request, f"Payment {payment.or_number} cannot be validated. It must be 'pending' and 'Gcash' method.")
            return self.form_invalid(form)


class PaymentCancelView(LoginRequiredMixin, KadamayRoleRequiredMixin, UpdateView):
    """
    View for 'Admin', 'Cashier', 'In-Charge' to cancel a payment.
    This sets the payment status to 'cancelled' and records who cancelled it.
    """
    model = Payment
    # Only allow status change to 'cancelled' and potentially a reason
    # Assuming you add a 'cancellation_reason' field to Payment model
    fields = ['status', 'cancellation_reason']
    # Simple form for cancellation confirmation
    template_name = 'payment/payment_cancel_form.html'
    success_url = reverse_lazy('payment:payment_list')
    # All can cancel, but admin might have more authority
    required_roles = ['Admin', 'Cashier', 'In-Charge']

    def form_valid(self, form):
        payment = form.instance
        if payment.status != 'cancelled':  # Prevent re-cancelling an already cancelled payment
            payment.status = 'cancelled'  # Set status to cancelled
            payment.cancelled_by = self.request.user
            payment.cancelled_at = timezone.now()  # Record cancellation timestamp
            messages.success(
                self.request, f"Payment {payment.or_number} cancelled successfully!")
            return super().form_valid(form)
        else:
            messages.warning(
                self.request, f"Payment {payment.or_number} is already cancelled.")
            return self.form_invalid(form)


# --- API Endpoints (Used for AJAX/JavaScript interactions) ---

def search_individuals_api(request):
    """
    API endpoint to search for individuals (payers) based on a query string.
    Returns a JSON list of individuals matching the query.
    """
    # IMPORT Individual MODEL HERE
    from apps.individual.models import Individual
    query = request.GET.get(
        'q', '')  # Get the search query from GET parameters
    individuals = []
    if query:
        # Filter individuals by first name, last name, or full name (case-insensitive)
        individuals_queryset = Individual.objects.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
            # Limit to 10 results
        ).values('id', 'first_name', 'last_name', 'middle_name', 'suffix', 'contact_number')[:10]

        for ind in individuals_queryset:
            # Construct full name from parts, handling missing middle_name/suffix
            full_name = f"{ind['first_name']} {ind.get('middle_name', '')} {ind['last_name']} {ind.get('suffix', '')}".strip(
            )
            individuals.append({
                'id': ind['id'],
                # Clean up extra spaces
                'full_name': full_name.replace('  ', ' ').strip(),
                'contact_number': ind['contact_number']
            })
    # Return data as JSON. safe=False is needed if you're returning a list directly.
    return JsonResponse(individuals, safe=False)


def get_individual_family_details_api(request, pk):
    """
    API endpoint to retrieve family members details for a given individual (payer).
    Used to pre-populate 'covered_members' options.
    """
    # IMPORT Individual MODEL HERE
    from apps.individual.models import Individual
    try:
        # Get the individual and prefetch their family and family members for efficiency
        individual = Individual.objects.prefetch_related(
            'family__family_members').get(pk=pk)
        family_members_data = []
        if individual.family:
            for member in individual.family.family_members.all():
                if member.id != individual.id:  # Exclude the payer themselves from covered members
                    full_name = f"{member.first_name} {member.middle_name if member.middle_name else ''} {member.last_name} {member.suffix if member.suffix else ''}".strip()
                    family_members_data.append({
                        'id': member.id,
                        'full_name': full_name.replace('  ', ' ').strip(),
                        # Assuming Individual model has get_relationship_display() for the relationship field
                        'relationship': member.get_relationship_display()
                    })
        return JsonResponse({'family_members': family_members_data})
    except Individual.DoesNotExist:
        return JsonResponse({'error': 'Individual not found'}, status=404)
    except Exception as e:
        # Generic error handling for other issues
        return JsonResponse({'error': str(e)}, status=500)


def get_contribution_type_details_api(request, pk):
    """
    API endpoint to get details of a specific contribution type (e.g., amount, description).
    """
    try:
        # Import inside function to avoid potential circular import issues if ContributionType
        # depends on something that also depends on Payment or Individual.
        from apps.contribution_type.models import ContributionType
        contribution_type = ContributionType.objects.get(pk=pk)
        data = {
            'id': contribution_type.id,
            'name': contribution_type.name,
            'description': contribution_type.description,
            # Add other relevant fields from ContributionType model, e.g., 'default_amount'
            # 'default_amount': contribution_type.default_amount,
        }
        return JsonResponse(data)
    except ContributionType.DoesNotExist:
        return JsonResponse({'error': 'Contribution Type not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
