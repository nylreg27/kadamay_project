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

        # FIXED: Add prefetch_related for head_of_family (kaniadto 'in_charge')
        # Ug prefetch 'members' para sa count
        queryset = queryset.prefetch_related('head_of_family', 'members').annotate(
            # 'members' ang related_name gikan sa Individual ngadto sa Family
            individual_count=Count('members')
        )

        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(family_name__icontains=search_query) |
                Q(address__icontains=search_query) |
                Q(church__name__icontains=search_query) |
                # NEW: Gitugotan ang pagpangita gamit ang ngalan sa ulo sa pamilya
                # <-- GI-CHANGE SA head_of_family
                Q(head_of_family__given_name__icontains=search_query) |
                # <-- GI-CHANGE SA head_of_family
                Q(head_of_family__surname__icontains=search_query)
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


class FamilyDetailView(LoginRequiredMixin, DetailView):
    model = Family
    template_name = 'family/family_detail.html'
    context_object_name = 'family'

    def get_queryset(self):
        # Pre-fetch ang head_of_family (kaniadto 'in_charge')
        # <-- GI-CHANGE SA head_of_family
        return super().get_queryset().prefetch_related('head_of_family', 'members')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        family = self.get_object()

        # Tanan nga individuals nga konektado niining pamilya
        all_individuals = family.members.all()

        context['total_members_count'] = all_individuals.count()
        context['active_members_count'] = all_individuals.filter(
            is_active_member=True, is_alive=True).count()
        context['deceased_members_count'] = all_individuals.filter(
            is_alive=False).count()

        # GI-FIX: Kuhaon direkta ang Ulo sa Pamilya gikan sa 'head_of_family' field sa Family
        # <-- GI-CHANGE SA head_of_family
        context['family_head'] = family.head_of_family

        # Kuhaon ang bag-ong bayad para sa mga miyembro niining pamilya
        context['family_payments'] = Payment.objects.filter(
            individual__family=family
        ).order_by('-date_paid')[:10]

        # Kwentahon ang kinatibuk-ang bayad nga gihimo sa mga miyembro niining pamilya
        context['total_family_contributions'] = Payment.objects.filter(
            individual__family=family
        ).aggregate(
            total_sum=Coalesce(Sum('amount'), Decimal(
                '0.00'), output_field=DecimalField())
        )['total_sum']

        # Kwentahon ang kinatibuk-ang kantidad nga gi-allocate sa mga miyembro niining pamilya
        total_allocated_payer_contributions = PaymentIndividualAllocation.objects.filter(
            individual__in=all_individuals,
            is_payer=True
        ).aggregate(
            total_sum=Coalesce(Sum('allocated_amount'), Decimal(
                '0.00'), output_field=DecimalField())
        )['total_sum']
        context['total_allocated_payer_contributions'] = total_allocated_payer_contributions

        # Ipasa usab ang all_individuals sa context para magamit sa template
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
        context['title'] = 'Paghimo Bag-ong Pamilya'
        return context

    def form_valid(self, form):
        messages.success(
            self.request, f"Pamilya '{form.instance.family_name}' malampusong nahimo!")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(
            self.request, "May sayop sa paghimo sa pamilya. Palihog susiha ang imong input.")
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
        context['title'] = f'Dugang Pamilya sa {church.name}'
        context['church'] = church
        return context

    def get_success_url(self):
        messages.success(
            self.request, f"Pamilya '{self.object.family_name}' nadugang sa {self.object.church.name} malampusong!")
        return reverse_lazy('church:church_detail', kwargs={'pk': self.kwargs['church_id']})

    def form_invalid(self, form):
        messages.error(
            self.request, "May sayop sa pagdugang sa pamilya. Palihog susiha ang imong input.")
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
            self.request, f"Pamilya '{self.object.family_name}' malampusong na-update!")
        return reverse_lazy('family:family_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'I-edit ang Pamilya: {self.object.family_name}'
        return context

    def form_invalid(self, form):
        messages.error(
            self.request, "May sayop sa pag-update sa pamilya. Palihog susiha ang imong input.")
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
            self.request, f"Pamilya '{self.object.family_name}' malampusong natangtang!")
        return super().form_valid(form)


class FamilyListInChurchView(LoginRequiredMixin, ListView):
    model = Family
    template_name = 'family/family_list.html'
    context_object_name = 'families'
    paginate_by = 10

    def get_queryset(self):
        church_id = self.kwargs.get('church_id')
        church = get_object_or_404(Church, pk=church_id)

        # FIXED: Add prefetch_related for head_of_family (kaniadto 'in_charge')
        queryset = Family.objects.filter(church=church).prefetch_related('head_of_family', 'members').annotate(
            individual_count=Count('members'))

        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(family_name__icontains=search_query) |
                Q(address__icontains=search_query) |
                # NEW: Gitugotan ang pagpangita gamit ang ngalan sa ulo sa pamilya
                # <-- GI-CHANGE SA head_of_family
                Q(head_of_family__given_name__icontains=search_query) |
                # <-- GI-CHANGE SA head_of_family
                Q(head_of_family__surname__icontains=search_query)
            )
        return queryset.order_by('family_name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        church_id = self.kwargs.get('church_id')
        church = get_object_or_404(Church, pk=church_id)
        context['church'] = church
        context['title'] = f'Mga Pamilya sa {church.name}'
        context['search_query'] = self.request.GET.get(
            'search', '')
        context['churches'] = Church.objects.all().order_by('name')
        context['selected_church'] = str(church_id)
        return context
