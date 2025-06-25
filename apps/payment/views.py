# apps/payment/views.py (Corrected Version)

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db import transaction # Para sa atomic operations
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages # Para sa user feedback
from django.utils import timezone # Para sa date/time stamps (e.g., date_validated)
from django.contrib.auth.models import Group # Para sa Django Groups based roles
from django.http import JsonResponse # Para sa API views
from django.db.models import Q, Max # Para sa complex queries (e.g., OR conditions sa search) ug Max aggregation
from django.views import View # Import View for class-based API views
from django.forms import inlineformset_factory # Para sa formsets

# Import Models from other apps
from apps.individual.models import Individual
from apps.family.models import FamilyMember # Needed for GetFamilyMembersAPIView
from apps.contribution_type.models import ContributionType

# Import Models and Forms from the current payment app
from .models import Payment, PaymentCoveredMember
from .forms import PaymentForm, CoveredMemberForm # CoveredMemberForm is now a defined class as per previous fix
from .utils import generate_next_or_number # For OR number generation

# --- Custom Mixin for KADAMAY Role-Based Access Control ---
class KadamayRoleRequiredMixin(UserPassesTestMixin):
    """
    Custom mixin to check for specific KADAMAY roles based on Django Groups.
    This is the most flexible way to manage "Admin", "Cashier", "In-Charge" roles.
    """
    required_roles = [] # List of role names (strings) allowed to access the view

    def test_func(self):
        user = self.request.user
        if not user.is_authenticated:
            return False
        if user.is_superuser: # Superusers always have access
            return True

        user_groups = user.groups.values_list('name', flat=True)
        for role_name in self.required_roles:
            if role_name in user_groups:
                return True
        return False

    def handle_no_permission(self):
        messages.warning(
            self.request, "You do not have the necessary permissions to access this page."
        )
        return redirect('login') # Or to a custom permission denied page


# --- Payment List View ---
class PaymentListView(LoginRequiredMixin, KadamayRoleRequiredMixin, ListView):
    model = Payment
    template_name = 'payment/payment_list.html'
    context_object_name = 'payments'
    paginate_by = 10

    required_roles = ['Admin', 'Cashier', 'In-Charge'] # Define roles for the mixin

    def get_queryset(self):
        queryset = super().get_queryset().order_by('-or_number') # Order by latest OR number
        
        # Optimize query for related data
        queryset = queryset.select_related(
            'individual', 'contribution_type', 'collected_by', 'validated_by', 'cancelled_by'
        ).prefetch_related(
            'covered_members__individual'
        )

        user = self.request.user
        user_groups = user.groups.values_list('name', flat=True)

        if user.is_superuser or 'Admin' in user_groups or 'Cashier' in user_groups:
            return queryset # Admin and Cashier see all payments
        elif 'In-Charge' in user_groups:
            # In-Charge sees payments they collected AND GCash payments pending validation
            return queryset.filter(
                Q(collected_by=user) | # Payments they collected
                Q(payment_method='GCASH', status='PENDING', is_validated=False) # GCash payments pending validation
            ).distinct() # Use distinct to avoid duplicate payments if they collected it and it's also pending validation
        else:
            return Payment.objects.none() # Regular users see no payments here

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_groups'] = self.request.user.groups.values_list('name', flat=True)
        return context

# --- Payment Detail View ---
class PaymentDetailView(LoginRequiredMixin, KadamayRoleRequiredMixin, DetailView):
    model = Payment
    template_name = 'payment/payment_detail.html'
    context_object_name = 'payment'
    required_roles = ['Admin', 'Cashier', 'In-Charge']

    def get_queryset(self):
        # Prefetch related data for efficiency
        queryset = super().get_queryset().select_related(
            'individual', 'contribution_type',
            'collected_by', 'validated_by', 'cancelled_by',
        ).prefetch_related(
            'covered_members',
            'covered_members__individual'
        )
        return queryset

# --- Payment Create View ---
class PaymentCreateView(LoginRequiredMixin, KadamayRoleRequiredMixin, CreateView):
    model = Payment
    form_class = PaymentForm
    template_name = 'payment/payment_form.html'
    success_url = reverse_lazy('payment:payment_list')
    required_roles = ['Admin', 'Cashier', 'In-Charge']

    # Define the formset here, using the correct CoveredMemberForm for PaymentCoveredMember
    PaymentCoveredMemberInlineFormSet = inlineformset_factory(
        Payment,
        PaymentCoveredMember,
        form=CoveredMemberForm, # Correctly referencing the CoveredMemberForm class
        extra=1, # Number of empty forms to display initially
        can_delete=True
    )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            # When POSTing, instantiate form and formset with POST data
            context['form'] = PaymentForm(self.request.POST)
            context['covered_member_formset'] = self.PaymentCoveredMemberInlineFormSet(
                self.request.POST, instance=self.object # instance=None for CreateView is fine here
            )
        else:
            # For GET requests, instantiate empty forms
            context['form'] = PaymentForm()
            # The OR number is now handled in PaymentForm's __init__ for new instances.
            
            context['covered_member_formset'] = self.PaymentCoveredMemberInlineFormSet(instance=self.object)
        return context

    def form_valid(self, form):
        # Set the user who collected the payment
        form.instance.collected_by = self.request.user
        
        payment_method = form.cleaned_data.get('payment_method')
        # Set initial status based on payment method
        # Use 'GCASH' (uppercase) for consistency with model choices
        form.instance.status = 'PENDING' if payment_method == 'GCASH' else 'PAID'
        
        # Set is_validated to True for CASH payments immediately
        if payment_method == 'CASH':
            form.instance.is_validated = True

        context = self.get_context_data()
        covered_member_formset = context['covered_member_formset']

        with transaction.atomic(): # Ensure both payment and covered members are saved or none
            self.object = form.save() # Save the main Payment instance first

            if covered_member_formset.is_valid():
                covered_member_formset.instance = self.object # Link formset to the saved Payment
                covered_member_formset.save() # Save covered members
                messages.success(
                    self.request, f"Payment OR#{self.object.or_number} and covered members saved successfully!"
                )
                return redirect(self.get_success_url())
            else:
                # If formset has errors, revert payment save and show form with errors
                messages.error(
                    self.request, "There were errors with the covered members. Please correct them."
                )
                return self.form_invalid(form) # Render form with errors

    def form_invalid(self, form):
        messages.error(self.request, "There were errors in the payment form. Please correct them.")
        context = self.get_context_data()
        context['form'] = form # Pass the form with errors
        # Re-initialize formset with POST data if available for errors to show up
        context['covered_member_formset'] = self.PaymentCoveredMemberInlineFormSet(
            self.request.POST, instance=self.object # For create, instance=None
        )
        return render(self.request, self.template_name, context)

# --- Payment Update View ---
class PaymentUpdateView(LoginRequiredMixin, KadamayRoleRequiredMixin, UpdateView):
    model = Payment
    form_class = PaymentForm
    template_name = 'payment/payment_form.html'
    context_object_name = 'payment'
    success_url = reverse_lazy('payment:payment_list')
    required_roles = ['Admin', 'Cashier', 'In-Charge']

    PaymentCoveredMemberInlineFormSet = inlineformset_factory(
        Payment,
        PaymentCoveredMember,
        form=CoveredMemberForm, # Correctly referencing the CoveredMemberForm class
        extra=1,
        can_delete=True
    )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['covered_member_formset'] = self.PaymentCoveredMemberInlineFormSet(
                self.request.POST, instance=self.object
            )
        else:
            context['covered_member_formset'] = self.PaymentCoveredMemberInlineFormSet(
                instance=self.object
            )
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        covered_member_formset = context['covered_member_formset']

        with transaction.atomic():
            self.object = form.save() # Save the main Payment instance

            if covered_member_formset.is_valid():
                covered_member_formset.instance = self.object # Link formset to the saved Payment
                covered_member_formset.save() # Save covered members
                messages.success(
                    self.request, f"Payment OR#{self.object.or_number} and covered members updated successfully!"
                )
                return redirect(self.get_success_url())
            else:
                messages.error(
                    self.request, "There were errors with the covered members. Please correct them."
                )
                return self.form_invalid(form)

    def form_invalid(self, form):
        messages.error(self.request, "There were errors in the payment form. Please correct them.")
        context = self.get_context_data()
        context['form'] = form
        # Re-initialize formset with POST data if available for errors to show up
        context['covered_member_formset'] = self.PaymentCoveredMemberInlineFormSet(
            self.request.POST, instance=self.object
        )
        return render(self.request, self.template_name, context)

# --- Payment Delete View ---
class PaymentDeleteView(LoginRequiredMixin, KadamayRoleRequiredMixin, DeleteView):
    model = Payment
    template_name = 'payment/payment_confirm_delete.html'
    context_object_name = 'payment'
    success_url = reverse_lazy('payment:payment_list')
    required_roles = ['Admin'] # Only Admin can delete

    def form_valid(self, form):
        messages.success(
            self.request, f"Payment OR#{self.get_object().or_number} deleted successfully!"
        )
        return super().form_valid(form)

# --- Payment Status Update Views (for Gcash validation / cancellation) ---

class PaymentValidateView(LoginRequiredMixin, KadamayRoleRequiredMixin, UpdateView):
    model = Payment
    # We only need the primary key to identify the object.
    # The status and validation fields are set by the view's logic, not user input.
    fields = [] # No fields needed from form for validation
    template_name = 'payment/payment_validate_form.html' # You might just need a confirmation page
    success_url = reverse_lazy('payment:payment_list')
    required_roles = ['Admin', 'In-Charge']

    def get_form(self, form_class=None):
        # We need a form to capture possible GCash reference number if it was missing/incorrect,
        # but the primary action is validation.
        # So we can create a minimal form here just for the reference number, if needed.
        # Or, just handle it in post without a form.
        # For simplicity, let's just use the default form but only expect PK.
        # If you need to allow IN-CHARGE to *input* a reference number, the form should have one field.
        # For now, let's assume the reference number is already on the Payment object.
        return super().get_form(form_class) # No specific form needed, just the instance

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        payment = self.object

        if payment.payment_method == 'GCASH' and payment.status == 'PENDING' and not payment.is_validated:
            # Admin or In-Charge validates the GCash payment
            payment.status = 'PAID'
            payment.is_validated = True
            payment.validated_by = self.request.user
            payment.date_validated = timezone.now() # Requires 'date_validated' field in Payment model
            payment.save()
            messages.success(
                self.request, f"GCash Payment OR#{payment.or_number} validated successfully! Status set to PAID."
            )
            return redirect(self.get_success_url())
        else:
            messages.error(
                self.request, 
                f"Payment OR#{payment.or_number} cannot be validated. "
                "It must be a 'GCASH' payment with 'PENDING' status and not yet validated."
            )
            return redirect(self.get_success_url()) # Redirect back or to a detail page


class PaymentCancelView(LoginRequiredMixin, KadamayRoleRequiredMixin, UpdateView):
    model = Payment
    # We need a form field for 'cancellation_reason'
    fields = ['cancellation_reason'] # Only allow updating the cancellation reason
    template_name = 'payment/payment_cancel_form.html' # A simple form to input reason
    success_url = reverse_lazy('payment:payment_list')
    required_roles = ['Admin', 'Cashier', 'In-Charge']

    def form_valid(self, form):
        payment = form.instance
        
        # Only allow cancellation if status is not already 'CANCELLED'
        if payment.status != 'CANCELLED':
            payment.status = 'CANCELLED'
            payment.cancelled_by = self.request.user
            payment.date_cancelled = timezone.now() # Requires 'date_cancelled' field in Payment model
            # cancellation_reason is already captured by the form.
            payment.save()
            messages.success(
                self.request, f"Payment OR#{payment.or_number} cancelled successfully!"
            )
            return redirect(self.get_success_url())
        else:
            messages.warning(
                self.request, f"Payment OR#{payment.or_number} is already cancelled."
            )
            return self.form_invalid(form) # Render form again with warning


# --- API Endpoints (Class-Based Views for AJAX/JavaScript interactions) ---

class IndividualSearchAPIView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        query = request.GET.get('q', '')
        individuals = Individual.objects.filter(
            Q(last_name__icontains=query) | Q(first_name__icontains=query) | # Search by name parts
            Q(contact_number__icontains=query)
        ).values('id', 'full_name', 'contact_number') # Ensure 'full_name' is a property/method in Individual model
        return JsonResponse(list(individuals), safe=False)

class GetFamilyMembersAPIView(LoginRequiredMixin, View):
    def get(self, request, individual_id, *args, **kwargs):
        try:
            payer = Individual.objects.get(pk=individual_id)
            
            # Assuming FamilyMember model has a ForeignKey to Individual and a ForeignKey to Family
            # And FamilyMember is related to a Family.
            payer_family_member = payer.familymember_set.filter(
                is_current_head=True # Assuming a field to identify the primary family link or head
            ).first() # Or pick the first one if no specific 'head' distinction

            family_members_data = []
            if payer_family_member and payer_family_member.family:
                # Get all individuals associated with the same family
                # Exclude the payer themselves
                family_members = Individual.objects.filter(
                    familymember__family=payer_family_member.family
                ).exclude(pk=individual_id).values('id', 'full_name') 
                
                family_members_data = list(family_members)
            
            return JsonResponse(family_members_data, safe=False)
        except Individual.DoesNotExist:
            return JsonResponse([], safe=False, status=404)
        except Exception as e:
            # In production, use proper logging (e.g., logging.error(f"Error: {e}"))
            print(f"Error in GetFamilyMembersAPIView: {e}") 
            return JsonResponse({'error': str(e)}, safe=False, status=500)

class GetNextOrNumberAPIView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        next_number = generate_next_or_number() # Use the utility function
        return JsonResponse({'next_or_number': str(next_number)})

# This function-based API view is kept as is, if you prefer it.
def get_contribution_type_details_api(request, pk):
    try:
        contribution_type = ContributionType.objects.get(pk=pk)
        data = {
            'id': contribution_type.id,
            'name': contribution_type.name,
            'description': contribution_type.description,
            # Add other relevant fields if needed, e.g., 'default_amount': contribution_type.default_amount
        }
        return JsonResponse(data)
    except ContributionType.DoesNotExist:
        return JsonResponse({'error': 'Contribution Type not found'}, status=404)
    except Exception as e:
        print(f"Error in get_contribution_type_details_api: {e}") # For debugging
        return JsonResponse({'error': str(e)}, status=500)

