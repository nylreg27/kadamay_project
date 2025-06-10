# apps/family/views.py
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.db.models import Q # Para sa search functionality

from .models import Family
from apps.church.models import Church # Import Church model
from .forms import FamilyForm

# --- Family List View ---
class FamilyListView(LoginRequiredMixin, ListView):
    model = Family
    template_name = 'family/family_list.html'
    context_object_name = 'families'
    paginate_by = 10 # Ilan ang ipapakita kada page

    def get_queryset(self):
        queryset = super().get_queryset()
        # Search functionality
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(family_name__icontains=search_query) |
                Q(address__icontains=search_query) |
                Q(church__name__icontains=search_query) # Search by church name
            )
        # Order by family_name by default
        return queryset.order_by('family_name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Pass the search query back to the template for the input field
        context['search_query'] = self.request.GET.get('search', '')
        return context


# --- Family Detail View ---
class FamilyDetailView(LoginRequiredMixin, DetailView):
    model = Family
    template_name = 'family/family_detail.html'
    context_object_name = 'family'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        family = self.get_object()
        
        # Calculate active and deceased members related to this family
        # Assuming Individual model has a ForeignKey to Family named 'family'
        # and has 'is_active_member' and 'is_alive' boolean fields.
        context['active_members_count'] = family.individual_set.filter(is_active_member=True, is_alive=True).count()
        context['deceased_members_count'] = family.individual_set.filter(is_alive=False).count()
        context['total_members_count'] = family.individual_set.count()

        return context


# --- Family Create View (General) ---
class FamilyCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Family
    form_class = FamilyForm
    template_name = 'family/family_form.html'
    success_url = reverse_lazy('family:family_list')

    def test_func(self):
        return self.request.user.is_superuser # Only superusers can create families generally

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create New Family'
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Family '{form.instance.family_name}' created successfully!")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "There was an error creating the family. Please check the form.")
        return super().form_invalid(form)


# --- Family Create View (In Church Context) ---
class FamilyCreateInChurchView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Family
    form_class = FamilyForm
    template_name = 'family/family_form.html'

    def test_func(self):
        return self.request.user.is_superuser # Only superusers can create families

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
        context['church'] = church # Pass church object for template display (e.g., title)
        return context
    
    def get_success_url(self):
        messages.success(self.request, f"Family '{self.object.family_name}' added to {self.object.church.name} successfully!")
        return reverse_lazy('church:church_detail', kwargs={'pk': self.kwargs['church_id']})

    def form_invalid(self, form):
        messages.error(self.request, "There was an error adding the family. Please check the form.")
        return super().form_invalid(form)


# --- Family Update View ---
class FamilyUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Family
    form_class = FamilyForm
    template_name = 'family/family_form.html'
    context_object_name = 'family' # Make sure context object is named 'family'
    
    def test_func(self):
        return self.request.user.is_superuser # Only superuser can edit

    def get_success_url(self):
        messages.success(self.request, f"Family '{self.object.family_name}' updated successfully!")
        return reverse_lazy('family:family_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edit Family: {self.object.family_name}'
        return context

    def form_invalid(self, form):
        messages.error(self.request, "There was an error updating the family. Please check the form.")
        return super().form_invalid(form)


# --- Family Delete View ---
class FamilyDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Family
    template_name = 'family/family_confirm_delete.html' # Create this template if you don't have one
    context_object_name = 'family'
    success_url = reverse_lazy('family:family_list')
    
    def test_func(self):
        return self.request.user.is_superuser # Only superuser can delete

    def form_valid(self, form):
        messages.success(self.request, f"Family '{self.object.family_name}' deleted successfully!")
        return super().form_valid(form)


# --- NEW: Family List by Church View ---
class FamilyListInChurchView(LoginRequiredMixin, ListView):
    model = Family
    template_name = 'family/family_list.html' # Re-use the existing family_list template
    context_object_name = 'families'
    paginate_by = 10

    def get_queryset(self):
        church_id = self.kwargs.get('church_id')
        church = get_object_or_404(Church, pk=church_id)
        
        # FIXED: Changed to church.family_set.all()
        queryset = church.family_set.all() 
        
        # Add search functionality if needed, similar to FamilyListView
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
        context['church'] = church # Pass the church object to the template
        context['title'] = f'Families of {church.name}' # Custom title for the page
        context['search_query'] = self.request.GET.get('search', '') # Pass search query
        return context

