# apps/family/views.py
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.db.models import Q, Count
from django.db.models import Sum, Case, When, DecimalField
from decimal import Decimal
from .models import Family
from apps.church.models import Church
from apps.individual.models import Individual
from apps.payment.models import Payment
from apps.payment.models import PaymentIndividualAllocation
from .forms import FamilyForm
from django.db.models.functions import Coalesce


class FamilyListView(LoginRequiredMixin, ListView):
    model = Family
    template_name = 'family/family_list.html'
    context_object_name = 'families'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()

        # Prefetch 'head_of_family' and 'members' for efficient access
        # 'members' is the related_name from Individual to Family
        queryset = queryset.prefetch_related('head_of_family', 'members').annotate(
            individual_count=Count('members')
        )

        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(family_name__icontains=search_query) |
                Q(address__icontains=search_query) |
                Q(church__name__icontains=search_query) |
                # Allow searching by head of family's first or last name
                Q(head_of_family__given_name__icontains=search_query) |
                Q(head_of_family__surname__icontains=search_query)
            )
        church_id = self.request.GET.get('church')
        if church_id:
            try:
                queryset = queryset.filter(church_id=int(church_id))
            except ValueError:
                pass  # Ignore invalid church_id in query
        return queryset.order_by('family_name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['churches'] = Church.objects.all().order_by('name')
        context['selected_church'] = self.request.GET.get('church', '')
        return context


class FamilyDetailView(LoginRequiredMixin, DetailView):
    model = Family
    template_name = 'family/family_detail.html'
    context_object_name = 'family'

    def get_queryset(self):
        # Pre-fetch 'head_of_family' and 'members' for efficient access
        return super().get_queryset().prefetch_related('head_of_family', 'members')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        family = self.get_object()

        # All individuals connected to this family
        all_individuals = family.members.all()

        context['total_members_count'] = all_individuals.count()
        context['active_members_count'] = all_individuals.filter(
            is_active_member=True, is_alive=True).count()
        context['deceased_members_count'] = all_individuals.filter(
            is_alive=False).count()

        # Get the Head of Family directly from the 'head_of_family' field on the Family instance
        context['family_head'] = family.head_of_family

        # Retrieve recent payments made by members of this family
        context['family_payments'] = Payment.objects.filter(
            individual__family=family
        ).order_by('-date_paid')[:10]  # Limit to 10 most recent payments

        # Calculate total contributions made by members of this family
        context['total_family_contributions'] = Payment.objects.filter(
            individual__family=family
        ).aggregate(
            total_sum=Coalesce(Sum('amount'), Decimal(
                '0.00'), output_field=DecimalField())
        )['total_sum']

        # Calculate the total amount allocated to members of this family (where they are the payer)
        total_allocated_payer_contributions = PaymentIndividualAllocation.objects.filter(
            individual__in=all_individuals,
            is_payer=True
        ).aggregate(
            total_sum=Coalesce(Sum('allocated_amount'), Decimal(
                '0.00'), output_field=DecimalField())
        )['total_sum']
        context['total_allocated_payer_contributions'] = total_allocated_payer_contributions

        # Pass all individuals to the context for use in the template
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
        context['title'] = 'Create New Family'  # English title for the page
        return context

    def form_valid(self, form):
        # Set the head_of_family field from the hidden input before saving
        # This is crucial because 'head_of_family_display' is not a model field
        head_of_family_id = self.request.POST.get('head_of_family')
        if head_of_family_id:
            form.instance.head_of_family = get_object_or_404(
                Individual, pk=head_of_family_id)
        else:
            form.instance.head_of_family = None  # Ensure it's set to None if not provided

        messages.success(
            self.request, f"Family '{form.instance.family_name}' successfully created!")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(
            self.request, "There was an error creating the family. Please check your input.")
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
        context['title'] = f'Add Family to {church.name}'  # English title
        context['church'] = church
        return context

    def get_success_url(self):
        messages.success(
            self.request, f"Family '{self.object.family_name}' successfully added to {self.object.church.name}!")
        return reverse_lazy('church:church_detail', kwargs={'pk': self.kwargs['church_id']})

    def form_valid(self, form):
        # Set the head_of_family field from the hidden input before saving
        head_of_family_id = self.request.POST.get('head_of_family')
        if head_of_family_id:
            form.instance.head_of_family = get_object_or_404(
                Individual, pk=head_of_family_id)
        else:
            form.instance.head_of_family = None  # Ensure it's set to None if not provided

        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(
            self.request, "There was an error adding the family. Please check your input.")
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
            self.request, f"Family '{self.object.family_name}' successfully updated!")
        return reverse_lazy('family:family_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # English title
        context['title'] = f'Edit Family: {self.object.family_name}'
        return context

    def form_valid(self, form):
        # Set the head_of_family field from the hidden input before saving
        head_of_family_id = self.request.POST.get('head_of_family')
        if head_of_family_id:
            form.instance.head_of_family = get_object_or_404(
                Individual, pk=head_of_family_id)
        else:
            form.instance.head_of_family = None  # Ensure it's set to None if not provided

        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(
            self.request, "There was an error updating the family. Please check your input.")
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
            self.request, f"Family '{self.object.family_name}' successfully deleted!")
        return super().form_valid(form)


class FamilyListInChurchView(LoginRequiredMixin, ListView):
    model = Family
    template_name = 'family/family_list.html'
    context_object_name = 'families'
    paginate_by = 10

    def get_queryset(self):
        church_id = self.kwargs.get('church_id')
        church = get_object_or_404(Church, pk=church_id)

        # Prefetch 'head_of_family' and 'members' for efficient access
        queryset = Family.objects.filter(church=church).prefetch_related('head_of_family', 'members').annotate(
            individual_count=Count('members'))

        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(family_name__icontains=search_query) |
                Q(address__icontains=search_query) |
                # Allow searching by head of family's first or last name
                Q(head_of_family__given_name__icontains=search_query) |
                Q(head_of_family__surname__icontains=search_query)
            )
        return queryset.order_by('family_name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        church_id = self.kwargs.get('church_id')
        church = get_object_or_404(Church, pk=church_id)
        context['church'] = church
        context['title'] = f'Families in {church.name}'  # English title
        context['search_query'] = self.request.GET.get(
            'search', '')
        context['churches'] = Church.objects.all().order_by('name')
        context['selected_church'] = str(church_id)
        return context
