# apps/individual/views.py
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.db.models import Q # Para sa search functionality
from apps.family.models import Family # Kailangan para sa Family model
from apps.church.models import Church # Import Church model (para sa filtering ng Individuals by Church)

from .models import Individual 
# from .forms import IndividualForm # IMPORTANT: Kailangan mo ring gumawa ng IndividualForm sa apps/individual/forms.py
from django import forms # Import forms module for the fallback IndividualForm

# Placeholder for IndividualForm (Assuming you will create this)
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
        messages.success(self.request, f"Member '{form.instance.given_name} {form.instance.surname}' created successfully!")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "There was an error creating the member. Please check the form.")
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
        messages.success(self.request, f"Member '{self.object.given_name} {self.object.surname}' updated successfully!")
        return reverse_lazy('individual:individual_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edit Member: {self.object.given_name} {self.object.surname}'
        return context

    def form_invalid(self, form):
        messages.error(self.request, "There was an error updating the member. Please check the form.")
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
        messages.success(self.request, f"Member '{self.object.given_name} {self.object.surname}' deleted successfully!")
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
            initial['family'] = family # Pre-fill the family field
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        family_id = self.kwargs.get('family_id')
        family = get_object_or_404(Family, pk=family_id)
        context['title'] = f'Add Member to {family.family_name}'
        context['family'] = family # Pass family object for template display
        return context
    
    def get_success_url(self):
        messages.success(self.request, f"Member '{self.object.given_name} {self.object.surname}' added to {self.object.family.family_name} successfully!")
        return reverse_lazy('family:family_detail', kwargs={'pk': self.kwargs['family_id']})

    def form_invalid(self, form):
        messages.error(self.request, "There was an error adding the member. Please check the form.")
        return super().form_invalid(form)

