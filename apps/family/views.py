# apps/family/views.py
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.db.models import Q, Count
# <-- Add Sum, Case, When, DecimalField for family_detail payments
from django.db.models import Sum, Case, When, DecimalField

from decimal import Decimal
from .models import Family
from apps.church.models import Church
# You might still need Individual for other contexts, keep it if so:
from apps.individual.models import Individual
from apps.payment.models import Payment  # <-- I-UNCOMMENT KINI NGA LINYA!
# <-- I-DUGANG KINI PARA SA ALOCATION
from apps.payment.models import PaymentIndividualAllocation
from .forms import FamilyForm
# <-- I-DUGANG KINI PARA SA Coalesce
from django.db.models.functions import Coalesce


class FamilyListView(LoginRequiredMixin, ListView):
    model = Family
    template_name = 'family/family_list.html'
    context_object_name = 'families'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()

        # --- NEW: Annotate individual_count for each family ---
        # Assuming your related_name for Family in Individual model is 'members'
        queryset = queryset.annotate(individual_count=Count('members'))
        # If your related_name is still default (individual_set), use Count('individual')

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
        return queryset.order_by('family_name')  # Already there, good!

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['churches'] = Church.objects.all().order_by('name')
        context['selected_church'] = self.request.GET.get('church', '')
        return context

# --- Family Detail View (NO CHANGES NEEDED FOR THE COUNT HERE, it's already working via direct access to individual_set/members.all().count()) ---


class FamilyDetailView(LoginRequiredMixin, DetailView):
    model = Family
    template_name = 'family/family_detail.html'
    context_object_name = 'family'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        family = self.get_object()

        # All individuals related to this family
        # FIXED: Changed family.individual_set.all() to family.members.all()
        all_individuals = family.members.all()  # Correct if related_name is 'members'

        context['total_members_count'] = all_individuals.count()

        context['active_members_count'] = all_individuals.filter(
            is_active_member=True, is_alive=True).count()

        context['deceased_members_count'] = all_individuals.filter(
            is_alive=False).count()

        # Get Family Head
        # Corrected to use 'HEAD' as per Individual model choices
        context['family_head'] = all_individuals.filter(
            relationship='HEAD').first()

        # Get recent payments for this family's members
        context['family_payments'] = Payment.objects.filter(
            individual__family=family
        ).order_by('-date_paid')[:10]

        # Calculate total payments made by members of this family
        # This aggregates the 'amount' field from the Payment model
        context['total_family_contributions'] = Payment.objects.filter(
            individual__family=family
        ).aggregate(
            total_sum=Coalesce(Sum('amount'), Decimal(
                '0.00'), output_field=DecimalField())
        )['total_sum']

        # Calculate total allocated amount to members of this family
        # from PaymentIndividualAllocation model where is_payer is True
        # This will filter PaymentIndividualAllocation records where the individual is a member of this family
        # AND they are marked as the payer.
        total_allocated_payer_contributions = PaymentIndividualAllocation.objects.filter(
            individual__in=all_individuals,  # Filter by individuals belonging to this family
            is_payer=True  # This field should now exist on PaymentIndividualAllocation
        ).aggregate(
            total_sum=Coalesce(Sum('allocated_amount'), Decimal(
                '0.00'), output_field=DecimalField())
        )['total_sum']
        context['total_allocated_payer_contributions'] = total_allocated_payer_contributions

        # Also pass all_individuals to the context for use in the template
        context['all_individuals'] = all_individuals

        return context


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


class FamilyListInChurchView(LoginRequiredMixin, ListView):
    model = Family
    template_name = 'family/family_list.html'
    context_object_name = 'families'
    paginate_by = 10

    def get_queryset(self):
        church_id = self.kwargs.get('church_id')
        church = get_object_or_404(Church, pk=church_id)

        # --- NEW: Annotate individual_count for families in a specific church ---
        # Again, use 'members' if that's your related_name
        queryset = Family.objects.filter(church=church).annotate(
            individual_count=Count('members'))

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
