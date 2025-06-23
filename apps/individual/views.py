# apps/individual/views.py

from django.views.generic import (
    CreateView, DetailView, ListView, UpdateView, DeleteView, View
)
from django.urls import reverse_lazy
from django.db.models import Q
from django.http import JsonResponse
import json

from apps.individual.models import Individual
from apps.church.models import Church
from apps.family.models import Family
# Import PaymentCoveredMember (assuming this is the class name you're using)
from apps.payment.models import PaymentCoveredMember, Payment
from apps.individual.forms import IndividualForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404


class IndividualListView(ListView):
    """
    Lists all Individual objects with search functionality.
    """
    model = Individual
    template_name = 'individual/individual_list.html'
    context_object_name = 'individuals'
    paginate_by = 10

    def get_queryset(self):
        """
        Returns the queryset for listing Individuals, ordered by surname and given name.
        Adds search functionality for full name, family name, church name,
        and now, membership ID.
        """
        queryset = super().get_queryset()

        # Prefetch related data for efficiency if displayed in the list
        queryset = queryset.select_related('family', 'church')

        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(given_name__icontains=search_query) |
                Q(middle_name__icontains=search_query) |
                Q(surname__icontains=search_query) |
                Q(contact_number__icontains=search_query) |
                Q(address__icontains=search_query) |
                Q(family__family_name__icontains=search_query) |
                Q(church__name__icontains=search_query) |
                Q(membership_id__icontains=search_query)
            )
        return queryset.order_by('surname', 'given_name')


class IndividualCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """
    View for creating a new Individual record.
    Requires user to be logged in and to be a superuser.
    """
    model = Individual
    form_class = IndividualForm
    template_name = 'individual/individual_form.html'
    success_url = reverse_lazy('individual:individual_list')

    def test_func(self):
        return self.request.user.is_superuser

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Add New Individual'
        return context

    def form_valid(self, form):
        return super().form_valid(form)


class IndividualUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    View for updating an existing Individual record.
    Requires user to be logged in and to be a superuser.
    """
    model = Individual
    form_class = IndividualForm
    template_name = 'individual/individual_form.html'
    success_url = reverse_lazy('individual:individual_list')

    def test_func(self):
        return self.request.user.is_superuser

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Update Individual Details'
        return context


class IndividualDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    View for deleting an Individual record.
    Requires user to be logged in and to be a superuser.
    """
    model = Individual
    template_name = 'individual/individual_confirm_delete.html'
    success_url = reverse_lazy('individual:individual_list')

    def test_func(self):
        return self.request.user.is_superuser


class IndividualDetailView(DetailView):
    """
    Detailed view for an Individual, designed to efficiently fetch all related
    payment information using prefetch_related for optimal database performance.
    """
    model = Individual
    template_name = 'individual/individual_detail.html'
    context_object_name = 'individual'

    def get_queryset(self):
        queryset = Individual.objects.all().prefetch_related(
            'payments_made__contribution_type',
            'payments_made__church', # Note: The Payment model doesn't directly link to Church in your provided models.py. This might cause issues later if not handled.
            # ETO NA ANG SAKTO NA RELATED_NAME!
            'paymentcoveredmember_set',
            'paymentcoveredmember_set__payment__contribution_type',
            'paymentcoveredmember_set__payment__church' # Note: The Payment model doesn't directly link to Church in your provided models.py. This might cause issues later if not handled.
        )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        individual = self.object

        combined_payments = []

        # The loop below now correctly accesses 'payments_made'
        for payment in individual.payments_made.all():
            combined_payments.append({
                'payment_type': 'Direct Payment',
                'receipt_number': payment.or_number,
                'amount': payment.amount,
                'allocated_amount': payment.amount, # Amount from the direct payment
                'date_paid': payment.date_paid,
                'contribution_type_name': payment.contribution_type.name if payment.contribution_type else 'N/A',
                'payment_status_display': payment.get_status_display(),
                'primary_payer_name': individual.full_name,
                'primary_payer_id': individual.pk,
                'payment_id': payment.pk,
            })

        # ETO NA ANG SAKTO NA RELATED_NAME!
        for allocation in individual.paymentcoveredmember_set.all():
            combined_payments.append({
                'payment_type': 'Allocation',
                'receipt_number': allocation.payment.or_number,
                'amount': allocation.payment.amount,
                'allocated_amount': allocation.amount_covered, # Here we access amount_covered from the allocation object
                'date_paid': allocation.payment.date_paid,
                'contribution_type_name': allocation.payment.contribution_type.name if allocation.payment.contribution_type else 'N/A',
                'payment_status_display': allocation.payment.get_status_display(),
                'primary_payer_name': allocation.payment.individual.full_name if allocation.payment.individual else 'N/A',
                'primary_payer_id': allocation.payment.individual.pk if allocation.payment.individual else None,
                'payment_id': allocation.payment.pk,
            })

        combined_payments.sort(key=lambda x: x['date_paid'], reverse=True)

        context['combined_payments'] = combined_payments
        return context


class IndividualListByChurchView(ListView):
    model = Individual
    template_name = 'individual/individual_list.html'
    context_object_name = 'individuals'
    paginate_by = 10

    def get_queryset(self):
        church_id = self.kwargs['church_id']
        queryset = Individual.objects.filter(church__id=church_id)

        # Prefetch related data for efficiency if displayed in the list
        queryset = queryset.select_related('family', 'church')

        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(given_name__icontains=search_query) |
                Q(middle_name__icontains=search_query) |
                Q(surname__icontains=search_query) |
                Q(contact_number__icontains=search_query) |
                Q(address__icontains=search_query) |
                Q(family__family_name__icontains=search_query) |
                Q(membership_id__icontains=search_query)
            )
        return queryset.order_by('surname', 'given_name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        church_id = self.kwargs['church_id']
        church = get_object_or_404(Church, pk=church_id)
        context['page_title'] = f'Members of {church.name}'
        context['current_church'] = church
        return context


class IndividualCreateForFamilyView(LoginRequiredMixin, CreateView):
    model = Individual
    form_class = IndividualForm
    template_name = 'individual/individual_form.html'

    def get_initial(self):
        initial = super().get_initial()
        family_id = self.kwargs.get('family_id')
        if family_id:
            initial['family'] = get_object_or_404(Family, pk=family_id)
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        family_id = self.kwargs.get('family_id')
        if family_id:
            family = get_object_or_404(Family, pk=family_id)
            context['page_title'] = f'Add Member to Family: {family.family_name}'
        else:
            context['page_title'] = 'Add New Individual'
        return context

    def get_success_url(self):
        family_id = self.kwargs.get('family_id')
        if family_id:
            return reverse_lazy('family:family_detail', kwargs={'pk': family_id})
        return reverse_lazy('individual:individual_list')


# NEW CLASS: API View for searching individuals by name or membership ID
class IndividualSearchAPIView(View):
    """
    API endpoint to search for Individual records by full name or membership ID.
    Returns results as a JSON array suitable for autocomplete/search suggestions.
    """

    def get(self, request, *args, **kwargs):
        query = request.GET.get('query', '')
        individuals = []

        if query:
            # Search by given name, middle name, surname, or membership_id
            # Using Q objects for OR conditions
            results = Individual.objects.filter(
                Q(given_name__icontains=query) |
                Q(middle_name__icontains=query) |
                Q(surname__icontains=query) |
                Q(membership_id__icontains=query)
            ).distinct()[:20] # Limit results to top 20 for performance

            for individual in results:
                individuals.append({
                    'id': individual.pk,
                    # Format for display
                    'text': f"{individual.full_name} ({individual.membership_id})"
                })

        # safe=False allows non-dict objects (like lists)
        return JsonResponse(individuals, safe=False)