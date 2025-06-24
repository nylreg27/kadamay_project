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
from django.contrib.auth.models import Group
from django.db.models import Q

# Import Individual and ContributionType models at the top (better practice)
from apps.individual.models import Individual
from apps.contribution_type.models import ContributionType

# Import ang Payment at CoveredMember models (KEEP THESE HERE, these are local to payment app)
from .models import Payment, PaymentCoveredMember
# Import ang PaymentForm at CoveredMemberFormSet (KEEP THESE HERE, these are local to payment app)
from .forms import PaymentCoveredMemberFormSet, PaymentForm
# Import the generate_next_or_number from utils.py
from .utils import generate_next_or_number

# --- Helper Function: OR Number Generation (REMOVED LOCAL FUNCTION, USING FROM UTILS) ---
# Ang generate_or_number function nga anaa unta dinhi gitangtang na.
# Karon gigamit na ang generate_next_or_number gikan sa .utils


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
        user_groups = user.groups.values_list('name', flat=True)
        for role_name in self.required_roles:
            if role_name in user_groups:
                return True

        # If the user is not a superuser and doesn't belong to any of the required groups
        return False

    def handle_no_permission(self):
        messages.warning(
            self.request, "You do not have the necessary permissions to access this page.")
        # Redirect to login page if no permission or to a permission denied page
        return redirect('login')


# --- Payment List View ---
# ADDED KadamayRoleRequiredMixin
class PaymentListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Payment
    template_name = 'payment/payment_list.html'
    context_object_name = 'payments'
    paginate_by = 10  # Adjust as needed

    def test_func(self):
        # Allow superusers, or users in 'Admin', 'Cashier', 'In-Charge' groups
        return self.request.user.is_superuser or \
            self.request.user.groups.filter(
                name__in=['Admin', 'Cashier', 'In-Charge']).exists()

    def get_queryset(self):
        # Filter payments based on user role
        if self.request.user.is_superuser or \
           self.request.user.groups.filter(name__in=['Admin', 'Cashier']).exists():
            return Payment.objects.all().order_by('-or_number')
        elif self.request.user.groups.filter(name='In-Charge').exists():
            # If 'In-Charge', only show payments where they are the collected_by or pending for them to validate
            return Payment.objects.filter(
                # Assuming 'In-Charge' can also see all pending payments
                Q(collected_by=self.request.user) | Q(status='pending')
            ).order_by('-or_number')
        else:
            return Payment.objects.none()  # Regular users see no payments here

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # HULAGWAY: Kani ang pinaka-importante nga part!
        # Kuhaa ang tanang group names sa user ug i-store sa 'user_groups'
        # para dali ra ma-access sa template.
        context['user_groups'] = self.request.user.groups.values_list(
            'name', flat=True)
        return context

# --- Payment Detail View ---
# ADDED KadamayRoleRequiredMixin


class PaymentDetailView(LoginRequiredMixin, KadamayRoleRequiredMixin, DetailView):
    """
    Displays the details of a single payment.
    Only Admin, Cashier, In-Charge roles can view this.
    Includes related covered members using prefetch_related for efficiency.
    """
    model = Payment
    template_name = 'payment/payment_detail.html'
    context_object_name = 'payment'
    # Roles allowed to view payment details
    required_roles = ['Admin', 'Cashier', 'In-Charge']

    def get_queryset(self):
        queryset = super().get_queryset().select_related(
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
    Uses a formset for multiple covered members. OR number is auto-generated by the form.
    """
    model = Payment
    form_class = PaymentForm
    template_name = 'payment/payment_form.html'
    success_url = reverse_lazy('payment:payment_list')
    required_roles = ['Admin', 'Cashier', 'In-Charge']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            # Explicitly pass request.POST to the main form
            context['form'] = PaymentForm(self.request.POST)
            context['covered_member_formset'] = PaymentCoveredMemberFormSet(
                self.request.POST, instance=self.object)
        else:
            # Create new form instance (will trigger OR generation)
            context['form'] = PaymentForm()
            context['covered_member_formset'] = PaymentCoveredMemberFormSet(
                instance=self.object)

        # No need to pass 'next_or_number' to context directly;
        # the form's __init__ method handles pre-filling it.
        return context

    def form_valid(self, form):
        # The OR number is handled by the form's __init__ method (pre-fill)
        # or by user's manual input. We don't overwrite it here.

        # The logged-in user collects the payment
        form.instance.collected_by = self.request.user

        # Determine initial payment status based on method (e.g., Gcash needs validation)
        payment_method = form.cleaned_data.get('payment_method')
        if payment_method == 'gcash':
            form.instance.status = 'pending'
        else:
            form.instance.status = 'paid'

        context = self.get_context_data()
        covered_member_formset = context['covered_member_formset']

        with transaction.atomic():
            self.object = form.save()  # Save the payment instance first

            if covered_member_formset.is_valid():
                covered_member_formset.instance = self.object
                covered_member_formset.save()
                messages.success(
                    # Updated message for null OR
                    self.request, f"Payment {self.object.or_number or 'without OR'} and covered members saved successfully!")
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
    required_roles = ['Admin', 'Cashier', 'In-Charge']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['covered_member_formset'] = PaymentCoveredMemberFormSet(
                self.request.POST, instance=self.object)
        else:
            context['covered_member_formset'] = PaymentCoveredMemberFormSet(
                instance=self.object)
        return context

    def form_valid(self, form):
        # No 'updated_by' field in Payment model, so skipping it.
        # If needed, add it to the model.
        # form.instance.updated_by = self.request.user

        context = self.get_context_data()
        covered_member_formset = context['covered_member_formset']

        with transaction.atomic():
            self.object = form.save()

            if covered_member_formset.is_valid():
                covered_member_formset.instance = self.object
                covered_member_formset.save()
                messages.success(
                    # Updated message for null OR
                    self.request, f"Payment {self.object.or_number or 'without OR'} and covered members updated successfully!")
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
    Only users with 'Admin' role can access this.
    """
    model = Payment
    template_name = 'payment/payment_confirm_delete.html'
    context_object_name = 'payment'
    success_url = reverse_lazy('payment:payment_list')
    required_roles = ['Admin']

    def form_valid(self, form):
        messages.success(
            # Updated message for null OR
            self.request, f"Payment {self.get_object().or_number or 'without OR'} deleted successfully!")
        return super().form_valid(form)


# --- Payment Status Update Views (for Gcash validation / cancellation) ---

class PaymentValidateView(LoginRequiredMixin, KadamayRoleRequiredMixin, UpdateView):
    """
    View for 'In-Charge' or 'Admin' to validate Gcash payments using a reference number.
    This changes the status from 'pending' to 'paid'.
    """
    model = Payment
    fields = ['status', 'gcash_reference_number']
    template_name = 'payment/payment_validate_form.html'
    success_url = reverse_lazy('payment:payment_list')
    required_roles = ['Admin', 'In-Charge']

    def form_valid(self, form):
        payment = form.instance
        if payment.status == 'pending' and payment.payment_method == 'gcash':
            payment.status = 'paid'
            payment.validated_by = self.request.user
            payment.date_validated = timezone.now()  # CORRECTED: Use date_validated
            messages.success(
                # Updated message for null OR
                self.request, f"Gcash Payment {payment.or_number or 'without OR'} validated successfully!")
            return super().form_valid(form)
        else:
            messages.error(
                # Updated message for null OR
                self.request, f"Payment {payment.or_number or 'without OR'} cannot be validated. It must be 'pending' and 'Gcash' method.")
            return self.form_invalid(form)


class PaymentCancelView(LoginRequiredMixin, KadamayRoleRequiredMixin, UpdateView):
    """
    View for 'Admin', 'Cashier', 'In-Charge' to cancel a payment.
    This sets the payment status to 'cancelled' and records who cancelled it.
    """
    model = Payment
    fields = ['status', 'cancellation_reason']
    template_name = 'payment/payment_cancel_form.html'
    success_url = reverse_lazy('payment:payment_list')
    required_roles = ['Admin', 'Cashier', 'In-Charge']

    def form_valid(self, form):
        payment = form.instance
        if payment.status != 'cancelled':
            payment.status = 'cancelled'
            payment.cancelled_by = self.request.user
            payment.date_cancelled = timezone.now()  # CORRECTED: Use date_cancelled
            messages.success(
                # Updated message for null OR
                self.request, f"Payment {payment.or_number or 'without OR'} cancelled successfully!")
            return super().form_valid(form)
        else:
            messages.warning(
                # Updated message for null OR
                self.request, f"Payment {payment.or_number or 'without OR'} is already cancelled.")
            return self.form_invalid(form)


# --- API Endpoints (Used for AJAX/JavaScript interactions) ---

def search_individuals_api(request):
    """
    API endpoint to search for individuals (payers) based on a query string.
    Returns a JSON list of individuals matching the query.
    """
    # Individual model is now imported at the top
    query = request.GET.get('q', '')
    individuals = []
    if query:
        individuals_queryset = Individual.objects.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        ).values('id', 'first_name', 'last_name', 'middle_name', 'suffix', 'contact_number')[:10]

        for ind in individuals_queryset:
            full_name = f"{ind['first_name']} {ind.get('middle_name', '')} {ind['last_name']} {ind.get('suffix', '')}".strip(
            )
            individuals.append({
                'id': ind['id'],
                'full_name': full_name.replace('  ', ' ').strip(),
                'contact_number': ind['contact_number']
            })
    return JsonResponse(individuals, safe=False)


def get_individual_family_details_api(request, pk):
    """
    API endpoint to retrieve family members details for a given individual (payer).
    Used to pre-populate 'covered_members' options.
    """
    # Individual model is now imported at the top
    try:
        individual = Individual.objects.prefetch_related(
            'family__family_members').get(pk=pk)
        family_members_data = []
        if individual.family:
            for member in individual.family.family_members.all():
                if member.id != individual.id:
                    full_name = f"{member.first_name} {member.middle_name if member.middle_name else ''} {member.last_name} {member.suffix if member.suffix else ''}".strip()
                    family_members_data.append({
                        'id': member.id,
                        'full_name': full_name.replace('  ', ' ').strip(),
                        'relationship': member.get_relationship_display()
                    })
        return JsonResponse({'family_members': family_members_data})
    except Individual.DoesNotExist:
        return JsonResponse({'error': 'Individual not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def get_contribution_type_details_api(request, pk):
    """
    API endpoint to get details of a specific contribution type (e.g., amount, description).
    """
    # ContributionType model is now imported at the top
    try:
        contribution_type = ContributionType.objects.get(pk=pk)
        data = {
            'id': contribution_type.id,
            'name': contribution_type.name,
            'description': contribution_type.description,
        }
        return JsonResponse(data)
    except ContributionType.DoesNotExist:
        return JsonResponse({'error': 'Contribution Type not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
