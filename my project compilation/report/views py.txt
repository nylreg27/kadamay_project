from django.views.generic import TemplateView
# <--- DUGANGI SUBQUERY UG OUTERREF DIRI!
from django.db.models import Sum, Count, Q, Case, When, DecimalField, Subquery, OuterRef
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
import json  # Para sa JSON serialization sa data sa charts
import datetime  # Para sa date calculations
from decimal import Decimal  # Import Decimal para sa type checking

# Import models from their respective apps
# Siguraduha nga sakto ni nga import path
from apps.individual.models import Individual
# Siguraduha nga sakto ni nga import path
from apps.family.models import Family
# Siguraduha nga sakto ni nga import path
from apps.church.models import Church
# Siguraduha nga sakto ni nga import path
from apps.payment.models import Payment, PaymentIndividualAllocation


class DashboardView(LoginRequiredMixin, TemplateView):

    template_name = 'report/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Title sa page
        context['title'] = 'Dashboard'

        # Filter by Church
        churches = Church.objects.all()
        context['churches'] = churches

        selected_church_id = self.request.GET.get('church')

        selected_church = None
        if selected_church_id:
            try:
                selected_church = Church.objects.get(id=selected_church_id)
                families = Family.objects.filter(church=selected_church)
                individuals = Individual.objects.filter(
                    family__church=selected_church)
                payments = Payment.objects.filter(
                    individual__family__church=selected_church)
            except Church.DoesNotExist:
                families = Family.objects.all()
                individuals = Individual.objects.all()
                payments = Payment.objects.all()
                selected_church_id = None  # Reset if church not found
        else:
            families = Family.objects.all()
            individuals = Individual.objects.all()
            payments = Payment.objects.all()

        # Importante para sa pre-selection sa dropdown
        context['selected_church'] = selected_church_id

        # Overall Statistics
        context['total_families'] = families.count()
        context['total_members'] = individuals.count()
        if selected_church_id:
            context['total_churches'] = 1 if selected_church else 0
        else:
            context['total_churches'] = churches.count()

        context['total_contributions'] = payments.aggregate(Sum('amount'))[
            'amount__sum'] or 0

        # Membership Status Distribution (for Pie Chart)
        membership_status_distribution = individuals.values(
            'membership_status').annotate(count=Count('id'))
        context['membership_status_distribution'] = {
            item['membership_status']: item['count'] for item in membership_status_distribution}

        # Contributions Over Time Chart
        # Example: Last 6 months contributions
        today = timezone.now()
        months_labels = []
        contributions_data = []
        for i in range(6):
            month_start = (today - datetime.timedelta(days=30*i)
                           ).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            month_end = (month_start + datetime.timedelta(days=30)).replace(day=1,
                                                                            hour=0, minute=0, second=0, microsecond=0) - datetime.timedelta(days=1)

            monthly_contributions = payments.filter(
                date_paid__gte=month_start,
                date_paid__lte=month_end
            ).aggregate(Sum('amount'))['amount__sum'] or 0

            # Add to front to show chronologically
            months_labels.insert(0, month_start.strftime('%b %Y'))
            # Add to front
            contributions_data.insert(0, monthly_contributions)

        context['contributions_over_time_labels'] = months_labels
        context['contributions_over_time_data'] = contributions_data

        # Top 5 Families with Most Members
        top_families = families.annotate(member_count=Count(
            'members')).order_by('-member_count')[:5]
        # Ensure family.church is included for display in template
        context['top_families_by_members'] = top_families.select_related(
            'church')

        # Top 5 Individual Contributors
        # FIX KINI GAMIT ANG SUBQUERY!
        # Subquery to calculate the sum of allocated_amount for each individual
        # where they are marked as the payer.
        payer_contributions_subquery = PaymentIndividualAllocation.objects.filter(
            # Links to the Individual in the outer query (Individual.id)
            individual=OuterRef('pk'),
            # Filter for allocations where this specific individual is the payer
            is_payer=True
        ).values('individual').annotate(
            # Sum the allocated_amount for these filtered allocations
            total_payer_amount=Sum('allocated_amount')
            # Select only the aggregated sum to be used in the outer query
        ).values('total_payer_amount')

        top_contributors = individuals.annotate(
            total_contribution=Subquery(
                payer_contributions_subquery, output_field=DecimalField())
        ).exclude(total_contribution__isnull=True).order_by('-total_contribution')[:5]
        # .exclude(total_contribution__isnull=True) will correctly filter out individuals
        # who have no payments where they are the payer, as the subquery will return NULL for them.
        context['top_individual_contributors'] = top_contributors.select_related(
            'family__church')

        # Church-wise Summary Table
        church_summaries = []
        for church_obj in churches:
            church_families = Family.objects.filter(church=church_obj)
            church_individuals = Individual.objects.filter(
                family__church=church_obj)
            church_payments = Payment.objects.filter(
                individual__family__church=church_obj)

            church_summaries.append({
                'name': church_obj.name,
                'total_families': church_families.count(),
                'total_members': church_individuals.count(),
                'total_contributions': church_payments.aggregate(Sum('amount'))['amount__sum'] or 0
            })
        context['church_summaries'] = church_summaries

        # JSON encode data for Chart.js (already done in your original template, but good to ensure)
        context['membership_status_distribution_json'] = json.dumps(
            context['membership_status_distribution'])
        context['contributions_over_time_labels_json'] = json.dumps(
            context['contributions_over_time_labels'])

        # CORRECTED SECTION: Convert Decimal values to float before JSON serialization
        # This loop iterates through the list of monthly contributions and converts each Decimal to float.
        converted_contributions_data = []
        for amount in context['contributions_over_time_data']:
            if isinstance(amount, Decimal):
                converted_contributions_data.append(float(amount))
            else:
                converted_contributions_data.append(amount)

        context['contributions_over_time_data_json'] = json.dumps(
            converted_contributions_data)

        # Ensure this is the last line of the method, no code after this.
        return context
