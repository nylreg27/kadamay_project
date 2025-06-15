# apps/individual/views.py

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db.models import Q  # <--- ADD THIS IMPORT!
from django.contrib import messages  # <--- ADD THIS IMPORT!
from apps.payment.models import Payment
from apps.individual.models import Individual
from apps.family.models import Family
from apps.church.models import Church
from .forms import IndividualForm
from .forms import PaymentForm

# Your existing IndividualDashboardView


class IndividualDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'individual/individual_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Consistent with your template title
        context['title'] = 'Kadamay Dashboard'

        # --- NEW ADDITION HERE ---
        # Fetch individuals just like your IndividualListView's get_queryset
        # to ensure the initial list in the dashboard is populated.
        context['individuals'] = Individual.objects.filter(
            is_active_member=True,
            is_alive=True
        ).order_by('surname', 'given_name')
        # --- END NEW ADDITION ---

        return context


@require_http_methods(["GET"])
@login_required
def individual_details_api(request, pk):
    try:
        individual = get_object_or_404(Individual, pk=pk)
        data = {
            'id': individual.id,
            'full_name': individual.full_name,
            'given_name': individual.given_name,
            'middle_name': individual.middle_name,
            'surname': individual.surname,
            'suffix_name': individual.suffix_name,
            # Check if 'code' still exists or should be 'membership_id'
            'membership_id': individual.membership_id,
            'relationship': individual.relationship,
            'membership_status': individual.membership_status,
            'is_alive': individual.is_alive,
            'is_active_member': individual.is_active_member,
            'family_id': individual.family.id if individual.family else None,
            'family_name': individual.family.family_name if individual.family and hasattr(individual.family, 'family_name') else "N/A",
            # Assuming Address is a separate model
            'municipality': individual.address.municipality if hasattr(individual, 'address') and individual.address else 'N/A',
            # Assuming Address is a separate model
            'barangay': individual.address.barangay if hasattr(individual, 'address') and individual.address else 'N/A',
        }
        return JsonResponse(data)
    except Individual.DoesNotExist:
        return JsonResponse({'error': 'Individual not found'}, status=404)
    except Exception as e:
        print(f"Error in individual_details_api: {e}")
        return JsonResponse({'error': str(e)}, status=500)

# Individual List View - MODIFIED FOR SEARCH


class IndividualListView(LoginRequiredMixin, ListView):
    model = Individual
    template_name = 'individual/individual_list.html'
    context_object_name = 'individuals'
    paginate_by = 10

    def get_queryset(self):
        # Start with the base queryset for active and alive members
        queryset = Individual.objects.filter(
            is_active_member=True, is_alive=True)

        # Get the search term from the GET request
        search_query = self.request.GET.get('search')

        if search_query:
            # Filter the queryset based on multiple fields (case-insensitive)
            # Using Q objects for OR conditions
            queryset = queryset.filter(
                Q(surname__icontains=search_query) |
                Q(given_name__icontains=search_query) |
                Q(middle_name__icontains=search_query) |
                Q(suffix_name__icontains=search_query) |
                # Changed from code to membership_id
                Q(membership_id__icontains=search_query) |
                # Search by related family's name
                Q(family__family_name__icontains=search_query) |
                # Search by related church's name
                Q(family__church__name__icontains=search_query)
            )

        # Order the results
        return queryset.order_by('surname', 'given_name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Changed title to 'Members' to match template
        context['title'] = 'Members'
        # Pass the current search query back to the template to retain the value in the search bar
        context['search_query'] = self.request.GET.get('search', '')
        return context

# Individual Detail View


class IndividualDetailView(LoginRequiredMixin, DetailView):
    model = Individual
    template_name = 'individual/individual_detail.html'
    context_object_name = 'individual'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Individual Details - {self.object.full_name}'
        return context

# Individual Create View


class IndividualCreateView(LoginRequiredMixin, CreateView):
    model = Individual
    form_class = IndividualForm
    template_name = 'individual/individual_form.html'
    success_url = reverse_lazy('individual:individual_list')
    extra_context = {'title': 'Add New Individual'}

    def form_valid(self, form):
        if not form.cleaned_data.get('membership_status'):
            form.instance.membership_status = 'ACTIVE'
        messages.success(self.request, "Individual added successfully!")
        return super().form_valid(form)

    def form_invalid(self, form):
        print("\n--- IndividualCreateView FORM IS INVALID! ---")
        print("Field errors:", form.errors)
        print("Non-field errors:", form.non_field_errors)
        print("-------------------------------------\n")
        messages.error(self.request, "Please correct the errors below.")
        return super().form_invalid(form)


# Individual Update View


class IndividualUpdateView(LoginRequiredMixin, UpdateView):
    model = Individual
    form_class = IndividualForm
    template_name = 'individual/individual_form.html'
    success_url = reverse_lazy('individual:individual_list')
    extra_context = {'title': 'Edit Individual'}  # Added for context

    def form_valid(self, form):
        messages.success(self.request, "Individual updated successfully!")
        return super().form_valid(form)

    def form_invalid(self, form):
        # --- ADD THESE PRINT STATEMENTS ---
        print("\n--- IndividualUpdateView FORM IS INVALID! ---")
        print("Field errors:", form.errors)
        print("Non-field errors:", form.non_field_errors)
        print("-------------------------------------\n")
        # --- END TEMPORARY PRINT STATEMENTS ---
        messages.error(self.request, "Please correct the errors below.")
        return super().form_invalid(form)

# Individual Delete View


class IndividualDeleteView(LoginRequiredMixin, DeleteView):
    model = Individual
    template_name = 'individual/individual_confirm_delete.html'
    success_url = reverse_lazy('individual:individual_list')

    def form_valid(self, form):
        messages.success(self.request, "Individual deleted successfully!")
        return super().form_valid(form)

# URL for listing individuals within a specific church - MODIFIED FOR SEARCH


class IndividualListInChurchView(LoginRequiredMixin, ListView):
    model = Individual
    template_name = 'individual/individual_list.html'
    context_object_name = 'individuals'

    def get_queryset(self):
        church_id = self.kwargs['church_id']
        church = get_object_or_404(Church, id=church_id)

        # Start with the base queryset for individuals in this church
        queryset = Individual.objects.filter(
            family__church=church,
            is_active_member=True,
            is_alive=True
        )

        # Add search filtering
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(surname__icontains=search_query) |
                Q(given_name__icontains=search_query) |
                Q(middle_name__icontains=search_query) |
                Q(suffix_name__icontains=search_query) |
                # Changed from code to membership_id
                Q(membership_id__icontains=search_query) |
                Q(family__family_name__icontains=search_query)
            )

        return queryset.order_by('surname', 'given_name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        church_id = self.kwargs['church_id']
        church = get_object_or_404(Church, id=church_id)
        context['title'] = f'Individuals in {church.name}'
        context['church'] = church
        context['search_query'] = self.request.GET.get(
            'search', '')  # Pass search query
        return context

# NEW URL: For creating an individual within a specific family context


class IndividualCreateInFamilyView(LoginRequiredMixin, CreateView):
    model = Individual
    form_class = IndividualForm
    template_name = 'individual/individual_form.html'

    def get_initial(self):
        initial = super().get_initial()
        family_id = self.kwargs.get('family_id')
        if family_id:
            initial['family'] = get_object_or_404(Family, id=family_id)
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        family_id = self.kwargs.get('family_id')
        if family_id:
            family = get_object_or_404(Family, id=family_id)
            context['title'] = f'Add Individual to {family.family_name}'
            context['family'] = family
        else:
            context['title'] = 'Add New Individual'
        return context

    def get_success_url(self):
        family_id = self.kwargs.get('family_id')
        if family_id:
            return reverse_lazy('family:family_detail', kwargs={'pk': family_id})
        return reverse_lazy('individual:individual_list')

    def form_valid(self, form):
        if not form.cleaned_data.get('membership_status'):
            form.instance.membership_status = 'ACTIVE'
        messages.success(self.request, "Individual added successfully!")
        return super().form_valid(form)

    def form_invalid(self, form):
        print("\n--- IndividualCreateInFamilyView FORM IS INVALID! ---")
        print("Field errors:", form.errors)
        print("Non-field errors:", form.non_field_errors)
        print("-------------------------------------\n")
        messages.error(self.request, "Please correct the errors below.")
        return super().form_invalid(form)


class PaymentCreateView(LoginRequiredMixin, CreateView):
    model = Payment
    form_class = PaymentForm  # You'll need to define this in apps/payment/forms.py
    template_name = 'payment/payment_form.html'  # Create this template

    def get_initial(self):
        initial = super().get_initial()
        # Get the individual_id from the URL kwargs
        individual_id = self.kwargs.get('individual_id')
        if individual_id:
            # Set the individual field in the form's initial data
            initial['individual'] = get_object_or_404(
                Individual, pk=individual_id)
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        individual_id = self.kwargs.get('individual_id')
        if individual_id:
            individual = get_object_or_404(Individual, pk=individual_id)
            context['title'] = f'Add Payment for {individual.full_name}'
            # Pass individual to template for display
            context['individual'] = individual
        else:
            context['title'] = 'Add New Payment'
        return context

    def form_valid(self, form):
        # The form's individual field should already be set by get_initial or user selection
        # If you want to automatically set the individual based on URL, ensure your form field is not required
        # or handle it here if it's hidden.
        messages.success(self.request, "Payment added successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        # Redirect back to the individual dashboard, or the individual's detail page
        individual_id = self.kwargs.get('individual_id')
        if individual_id:
            # Assuming your individual dashboard URL structure allows for a direct return
            # Or you might want to return to individual:individual_detail if you have one.
            return reverse_lazy('individual:individual_dashboard')
            # return reverse_lazy('individual:individual_detail', kwargs={'pk': individual_id})
        return reverse_lazy('individual:individual_list')  # Fallback
