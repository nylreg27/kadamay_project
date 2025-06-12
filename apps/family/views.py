# apps/family/views.py
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.db.models import Q  # Para sa search functionality
from django.db.models import F  # Para sa mas efficient na filtering

from .models import Family
from apps.church.models import Church  # Import Church model
# IMPORT INDIVIDUAL AND PAYMENT MODELS KUNG WALA PA (ASSUMING NASA APPS/INDIVIDUAL at APPS/PAYMENT SILA)
from apps.individual.models import Individual  # Import Individual model
from apps.payment.models import Payment  # Import Payment model
from .forms import FamilyForm

# --- Family List View (NO CHANGES HERE) ---


class FamilyListView(LoginRequiredMixin, ListView):
    model = Family
    template_name = 'family/family_list.html'
    context_object_name = 'families'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(family_name__icontains=search_query) |
                Q(address__icontains=search_query) |
                Q(church__name__icontains=search_query)
            )
        church_id = self.request.GET.get('church')
        if church_id:
            try:
                queryset = queryset.filter(church_id=int(church_id))
            except ValueError:
                pass
        return queryset.order_by('family_name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['churches'] = Church.objects.all().order_by('name')
        context['selected_church'] = self.request.GET.get('church', '')
        return context


# --- Family Detail View (MODIFIED) ---
class FamilyDetailView(LoginRequiredMixin, DetailView):
    model = Family
    template_name = 'family/family_detail.html'
    context_object_name = 'family'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        family = self.get_object()

        # Optimize queries by prefetching related data
        # Use select_related for ForeignKey relationships and prefetch_related for ManyToMany or reverse ForeignKeys
        # For Individual and Payment, it's a reverse ForeignKey, so prefetch_related is correct.
        # But for counting, direct filtering on individual_set is efficient enough.

        # Calculate active and deceased members related to this family
        # Assuming Individual model has a ForeignKey to Family named 'family'
        # and has 'is_active_member' and 'is_alive' boolean fields.

        # All individuals related to this family
        all_individuals = family.individual_set.all()

        context['total_members_count'] = all_individuals.count()

        context['active_members_count'] = all_individuals.filter(
            is_active_member=True, is_alive=True).count()

        context['deceased_members_count'] = all_individuals.filter(
            is_alive=False).count()

        # Get Family Head
        # Assuming 'relationship' field in Individual model defines 'HEAD'
        # Use .first() to get a single object or None if not found
        context['family_head'] = all_individuals.filter(
            relationship='H').first()
        # Note: Make sure 'H' matches the exact value in your Individual model for Family Head.
        # You might need to change 'H' to 'HEAD' if that's what's stored in your database.
        # Based on your image, it looks like 'HEAD' is stored. So, let's change this to 'HEAD'.
        # Correction: Looking at image_21c96d.png, the relationship column actually says 'HEAD' directly.
        # So, change 'H' to 'HEAD' to match your database.

        context['family_head'] = all_individuals.filter(
            relationship='HEAD').first()  # Corrected based on DB screenshot

        # Get recent payments for this family's members
        # Assuming Payment model has a ForeignKey to Individual, and Individual has a ForeignKey to Family
        # We want payments related to *any* individual within this family.
        context['family_payments'] = Payment.objects.filter(
            individual__family=family
            # Get latest 10 payments, adjust as needed
        ).order_by('-date_paid')[:10]

        return context


# --- Family Create View (General) (NO CHANGES HERE) ---
class FamilyCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Family
    form_class = FamilyForm
    template_name = 'family/family_form.html'
    success_url = reverse_lazy('family:family_list')

    def test_func(self):
        return self.request.user.is_superuser

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create New Family'
        return context

    def form_valid(self, form):
        messages.success(
            self.request, f"Family '{form.instance.family_name}' created successfully!")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(
            self.request, "There was an error creating the family. Please check the form.")
        return super().form_invalid(form)


# --- Family Create View (In Church Context) (NO CHANGES HERE) ---
class FamilyCreateInChurchView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Family
    form_class = FamilyForm
    template_name = 'family/family_form.html'

    def test_func(self):
        return self.request.user.is_superuser

    def get_initial(self):
        initial = super().get_initial()
        church_id = self.kwargs.get('church_id')
        if church_id:
            church = get_object_or_404(Church, pk=church_id)
            initial['church'] = church
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        church_id = self.kwargs.get('church_id')
        church = get_object_or_404(Church, pk=church_id)
        context['title'] = f'Add Family to {church.name}'
        context['church'] = church
        return context

    def get_success_url(self):
        messages.success(
            self.request, f"Family '{self.object.family_name}' added to {self.object.church.name} successfully!")
        return reverse_lazy('church:church_detail', kwargs={'pk': self.kwargs['church_id']})

    def form_invalid(self, form):
        messages.error(
            self.request, "There was an error adding the family. Please check the form.")
        return super().form_invalid(form)


# --- Family Update View (NO CHANGES HERE) ---
class FamilyUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Family
    form_class = FamilyForm
    template_name = 'family/family_form.html'
    context_object_name = 'family'

    def test_func(self):
        return self.request.user.is_superuser

    def get_success_url(self):
        messages.success(
            self.request, f"Family '{self.object.family_name}' updated successfully!")
        return reverse_lazy('family:family_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edit Family: {self.object.family_name}'
        return context

    def form_invalid(self, form):
        messages.error(
            self.request, "There was an error updating the family. Please check the form.")
        return super().form_invalid(form)


# --- Family Delete View (NO CHANGES HERE) ---
class FamilyDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Family
    template_name = 'family/family_confirm_delete.html'
    context_object_name = 'family'
    success_url = reverse_lazy('family:family_list')

    def test_func(self):
        return self.request.user.is_superuser

    def form_valid(self, form):
        messages.success(
            self.request, f"Family '{self.object.family_name}' deleted successfully!")
        return super().form_valid(form)


# --- NEW: Family List by Church View (NO CHANGES HERE) ---
class FamilyListInChurchView(LoginRequiredMixin, ListView):
    model = Family
    template_name = 'family/family_list.html'
    context_object_name = 'families'
    paginate_by = 10

    def get_queryset(self):
        church_id = self.kwargs.get('church_id')
        church = get_object_or_404(Church, pk=church_id)
        queryset = Family.objects.filter(church=church)
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(family_name__icontains=search_query) |
                Q(address__icontains=search_query)
            )
        return queryset.order_by('family_name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        church_id = self.kwargs.get('church_id')
        church = get_object_or_404(Church, pk=church_id)
        context['church'] = church
        context['title'] = f'Families of {church.name}'
        context['search_query'] = self.request.GET.get(
            'search', '')
        context['churches'] = Church.objects.all().order_by('name')
        context['selected_church'] = str(church_id)
        return context
