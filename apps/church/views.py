# apps/church/views.py (Full and Corrected Version)

from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from .models import Church, District  # Ensure District is imported
from apps.family.models import Family
from apps.individual.models import Individual

# --- Church List View (PRIORITY IS CHURCH NAME/ADDRESS/DISTRICT SEARCH ONLY) ---


class ChurchListView(LoginRequiredMixin, ListView):
    model = Church
    template_name = 'church/church_list.html'
    context_object_name = 'churches'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get('search')

        if search_query:
            # ONLY search on fields directly related to the Church and its District
            # All 'in_charge' related search conditions are intentionally removed here
            # as per your request for church name/address/district priority.
            queryset = queryset.filter(
                Q(name__icontains=search_query) |      # Search by church name
                # Search by church address
                Q(address__icontains=search_query) |
                # Search by district name
                Q(district__name__icontains=search_query)
            ).distinct()
        return queryset.order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        return context


# --- Church Detail View ---
class ChurchDetailView(LoginRequiredMixin, DetailView):
    model = Church
    template_name = 'church/church_detail.html'
    context_object_name = 'church'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        church = self.get_object()

        # Calculate counts for Quick Stats
        context['total_families_count'] = church.families.count()
        context['total_members_count'] = Individual.objects.filter(
            family__church=church).count()

        context['active_members_count'] = Individual.objects.filter(
            family__church=church,
            is_active_member=True,
            is_alive=True
        ).count()
        context['deceased_members_count'] = Individual.objects.filter(
            family__church=church,
            is_alive=False
        ).count()

        # Get recent families (e.g., first 5)
        context['recent_families'] = church.families.order_by('-id')[:5]

        # Get recent members through families belonging to this church (e.g., first 5)
        context['recent_members'] = Individual.objects.filter(
            family__church=church).order_by('-id')[:5]

        return context


# --- Church Create View ---
class ChurchCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Church
    fields = ['name', 'address', 'district', 'in_charge', 'is_active']
    template_name = 'church/church_form.html'
    success_url = reverse_lazy('church:church_list')

    def test_func(self):
        return self.request.user.is_superuser

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create New Church'
        return context

    def form_valid(self, form):
        messages.success(
            self.request, f"Church '{form.instance.name}' created successfully!")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(
            self.request, "There was an error creating the church. Please check the form.")
        return super().form_invalid(form)


# --- Church Update View ---
class ChurchUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Church
    fields = ['name', 'address', 'district', 'in_charge', 'is_active']
    template_name = 'church/church_form.html'
    context_object_name = 'church'

    def test_func(self):
        return self.request.user.is_superuser

    def get_success_url(self):
        messages.success(
            self.request, f"Church '{self.object.name}' updated successfully!")
        return reverse_lazy('church:church_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edit Church: {self.object.name}'
        return context

    def form_invalid(self, form):
        messages.error(
            self.request, "There was an error updating the church. Please check the form.")
        return super().form_invalid(form)


# --- Church Delete View ---
class ChurchDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Church
    template_name = 'church/church_confirm_delete.html'
    context_object_name = 'church'
    success_url = reverse_lazy('church:church_list')

    def test_func(self):
        return self.request.user.is_superuser

    def form_valid(self, form):
        messages.success(
            self.request, f"Church '{self.object.name}' deleted successfully!")
        return super().form_valid(form)


# --- Family List in Church View ---
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
            # Here, we only search family's own fields (family_name, address)
            # If you want to search by a family member's name (Individual model),
            # you would need to add something like:
            # Q(members__given_name__icontains=search_query) |
            # Q(members__surname__icontains=search_query)
            queryset = queryset.filter(
                Q(family_name__icontains=search_query) |
                Q(address__icontains=search_query)
            ).distinct()  # Add distinct() here if you add more complex joins
        return queryset.order_by('family_name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        church_id = self.kwargs.get('church_id')
        church = get_object_or_404(Church, pk=church_id)
        context['church'] = church
        context['title'] = f'Families in {church.name}'
        context['search_query'] = self.request.GET.get('search', '')
        return context


# --- Family Create in Church View ---
class FamilyCreateInChurchView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Family
    # Assuming Family has an 'in_charge' field (e.g., a leader from Individual)
    fields = ['family_name', 'address', 'in_charge', 'is_active']
    template_name = 'family/family_form.html'

    def test_func(self):
        return self.request.user.is_superuser

    def get_initial(self):
        initial = super().get_initial()
        church_id = self.kwargs.get('church_id')
        if church_id:
            church = get_object_or_404(Church, pk=church_id)
            # Automatically set the church for the new family
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


# --- Dashboard View ---
def dashboard(request):
    """
    Isang simpleng view function para sa dashboard.
    Kailangan mong lumikha ng template file sa
    templates/church/dashboard.html
    """
    context = {
        'title': 'Church Dashboard',
        'message': 'Welcome to the Church Dashboard!',
    }
    return render(request, 'church/dashboard.html', context)
