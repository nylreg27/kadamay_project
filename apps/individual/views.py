# apps/individual/views.py
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django import forms
from django.db import models

# --- Import your models ---
from .models import Individual
from apps.family.models import Family
from apps.church.models import Church
# Corrected: Import Payment model from apps.payment.models
from apps.payment.models import Payment

# --- Placeholder for IndividualForm ---
try:
    from .forms import IndividualForm
except ImportError:
    print("Warning: IndividualForm not found. Please create apps/individual/forms.py")

    class IndividualForm(forms.ModelForm):
        class Meta:
            model = Individual
            fields = '__all__'

# --- Individual List View ---


class IndividualListView(LoginRequiredMixin, ListView):
    model = Individual
    template_name = 'individual/individual_list.html'
    context_object_name = 'individuals'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(given_name__icontains=search_query) |
                Q(surname__icontains=search_query) |
                Q(middle_name__icontains=search_query) |
                Q(family__family_name__icontains=search_query) |
                Q(family__church__name__icontains=search_query)
            )
        return queryset.order_by('surname', 'given_name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        return context


# --- Individual Detail View ---
class IndividualDetailView(LoginRequiredMixin, DetailView):
    model = Individual
    template_name = 'individual/individual_detail.html'
    context_object_name = 'individual'


# --- Individual Create View (General) ---
class IndividualCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Individual
    form_class = IndividualForm
    template_name = 'individual/individual_form.html'
    success_url = reverse_lazy('individual:individual_list')

    def test_func(self):
        return self.request.user.is_superuser

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create New Member'
        return context

    def form_valid(self, form):
        messages.success(
            self.request, f"Member '{form.instance.given_name} {form.instance.surname}' created successfully!")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(
            self.request, "There was an error creating the member. Please check the form.")
        return super().form_invalid(form)


# --- Individual Update View ---
class IndividualUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Individual
    form_class = IndividualForm
    template_name = 'individual/individual_form.html'
    context_object_name = 'individual'

    def test_func(self):
        return self.request.user.is_superuser

    def get_success_url(self):
        messages.success(
            self.request, f"Member '{self.object.given_name} {self.object.surname}' updated successfully!")
        return reverse_lazy('individual:individual_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edit Member: {self.object.given_name} {self.object.surname}'
        return context

    def form_invalid(self, form):
        messages.error(
            self.request, "There was an error updating the member. Please check the form.")
        return super().form_invalid(form)


# --- Individual Delete View ---
class IndividualDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Individual
    template_name = 'individual/individual_confirm_delete.html'
    context_object_name = 'individual'
    success_url = reverse_lazy('individual:individual_list')

    def test_func(self):
        return self.request.user.is_superuser

    def form_valid(self, form):
        messages.success(
            self.request, f"Member '{self.object.given_name} {self.object.surname}' deleted successfully!")
        return super().form_valid(form)


# --- Individual List by Church View ---
class IndividualListInChurchView(LoginRequiredMixin, ListView):
    model = Individual
    template_name = 'individual/individual_list.html'
    context_object_name = 'individuals'
    paginate_by = 10

    def get_queryset(self):
        church_id = self.kwargs.get('church_id')
        church = get_object_or_404(Church, pk=church_id)

        queryset = Individual.objects.filter(family__church=church)

        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(given_name__icontains=search_query) |
                Q(surname__icontains=search_query) |
                Q(middle_name__icontains=search_query) |
                Q(family__family_name__icontains=search_query)
            )
        return queryset.order_by('surname', 'given_name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        church_id = self.kwargs.get('church_id')
        church = get_object_or_404(Church, pk=church_id)
        context['church'] = church
        context['title'] = f'Members of {church.name}'
        context['search_query'] = self.request.GET.get('search', '')
        return context


# --- BAGONG VIEW: Individual Create View (In Family Context) ---
class IndividualCreateInFamilyView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Individual
    form_class = IndividualForm
    template_name = 'individual/individual_form.html'

    def test_func(self):
        return self.request.user.is_superuser

    def get_initial(self):
        initial = super().get_initial()
        family_id = self.kwargs.get('family_id')
        if family_id:
            family = get_object_or_404(Family, pk=family_id)
            initial['family'] = family
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        family_id = self.kwargs.get('family_id')
        family = get_object_or_404(Family, pk=family_id)
        context['title'] = f'Add Member to {family.family_name}'
        context['family'] = family
        return context

    def get_success_url(self):
        messages.success(
            self.request, f"Member '{self.object.given_name} {self.object.surname}' added to {self.object.family.family_name} successfully!")
        return reverse_lazy('family:family_detail', kwargs={'pk': self.kwargs['family_id']})

    def form_invalid(self, form):
        messages.error(
            self.request, "There was an error adding the member. Please check the form.")
        return super().form_invalid(form)


# NEW: Dashboard View
class IndividualDashboardView(LoginRequiredMixin, ListView):
    model = Individual
    template_name = 'individual/individual_dashboard.html'
    context_object_name = 'individuals'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(given_name__icontains=search_query) |
                Q(middle_name__icontains=search_query) |
                Q(surname__icontains=search_query)
            )
        return queryset.order_by('surname', 'given_name')


# NEW: API View to get individual details (for AJAX)
def individual_details_api(request, pk):
    individual = get_object_or_404(Individual, pk=pk)

    # Calculate total contribution amount and latest contribution date
    total_contribution = individual.payments.aggregate(models.Sum('amount'))[
        'amount__sum'] or 0
    latest_payment = individual.payments.order_by('-date_paid').first()
    latest_contribution_date = latest_payment.date_paid.strftime(
        '%Y-%m-%d') if latest_payment else 'N/A'

    data = {
        # Added 'N/A' for clarity if null
        'membership_id': individual.membership_id or 'N/A',
        'contact_no': individual.contact_number or 'N/A',  # Use contact_number
        'full_name': f"{individual.surname}, {individual.given_name} {individual.middle_name or ''} {individual.suffix_name or ''}".strip(),
        'address': individual.address or 'N/A',  # Added 'N/A' for clarity if null
        'is_alive': individual.is_alive,
        'is_active_member': individual.is_active_member,
        'church_name': individual.family.church.name if individual.family and individual.family.church else 'N/A',
        'district_name': individual.family.church.district.name if individual.family and individual.family.church and individual.family.church.district else 'N/A',
        # Convert Decimal to string
        'contribution_amount': str(total_contribution),
        'contribution_date': latest_contribution_date,
    }

    payments = individual.payments.all().order_by('-date_paid')  # Use date_paid
    data['payments'] = [
        {
            # Use date_paid
            'date': payment.date_paid.strftime('%Y-%m-%d') if payment.date_paid else 'N/A',
            # Use contribution_type name as description
            'description': payment.contribution_type.name,
            'amount': str(payment.amount),
            # Use remarks as receipt_no (if that's where it's stored)
            'receipt_no': payment.remarks or 'N/A',
        } for payment in payments
    ]

    data['family_members'] = []
    if individual.family:
        # Exclude the current individual from their own family list
        family_members = individual.family.individual_set.all().exclude(
            pk=individual.pk).order_by('surname', 'given_name')
        data['family_members'] = [
            {
                'code': fam_member.membership_id or 'N/A',
                'full_name': f"{fam_member.surname}, {fam_member.given_name} {fam_member.middle_name or ''}".strip(),
                'membership_status': 'Active' if fam_member.is_active_member else 'Inactive',
                'status': 'Alive' if fam_member.is_alive else 'Deceased',
                'relationship': fam_member.get_relationship_display(),
            } for fam_member in family_members
        ]

    return JsonResponse(data)
