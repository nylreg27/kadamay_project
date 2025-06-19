# apps/report/views.py

from django.views.generic import TemplateView
from django.db.models import Sum, Count, Q, Case, When, DecimalField, Subquery, OuterRef
from django.db.models.functions import Coalesce, ExtractMonth, ExtractYear # Added for robust date filtering
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
import json
import datetime
from decimal import Decimal # Make sure this import is there!

# Import models from their respective apps
from apps.individual.models import Individual
from apps.family.models import Family
from apps.church.models import Church
from apps.payment.models import Payment, CoveredMember # Ensure CoveredMember is imported

class DashboardView(LoginRequiredMixin, TemplateView):

    template_name = 'report/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['title'] = 'Dashboard'

        churches = Church.objects.all()
        context['churches'] = churches

        selected_church_id = self.request.GET.get('church')

        # Initialize base querysets
        families_queryset = Family.objects.all()
        individuals_queryset = Individual.objects.all()
        payments_queryset = Payment.objects.all()
        covered_members_queryset = CoveredMember.objects.all() # New: for CoveredMember data

        selected_church = None
        if selected_church_id:
            try:
                selected_church = Church.objects.get(id=selected_church_id)
                families_queryset = families_queryset.filter(church=selected_church)
                individuals_queryset = individuals_queryset.filter(family__church=selected_church)
                # Assuming Payment has a direct ForeignKey to Church
                payments_queryset = payments_queryset.filter(church=selected_church)
                # Filter CoveredMember through its payment's church
                covered_members_queryset = covered_members_queryset.filter(payment__church=selected_church) 

            except Church.DoesNotExist:
                # If church not found, use all data but ensure selected_church_id is None
                selected_church_id = None
        
        context['selected_church'] = selected_church_id

        # Overall Statistics
        context['total_families'] = families_queryset.count()
        context['total_members'] = individuals_queryset.count()
        context['total_churches'] = 1 if selected_church else churches.count() # Simplified logic

        # Fix: Change 0 to Decimal(0)
        context['total_contributions'] = payments_queryset.aggregate(total=Coalesce(Sum('amount'), Decimal(0)))['total']

        # Membership Status Distribution (for Pie Chart)
        membership_status_distribution = individuals_queryset.values(
            'membership_status').annotate(count=Count('id'))
        context['membership_status_distribution'] = {
            item['membership_status']: item['count'] for item in membership_status_distribution
        }

        # Contributions Over Time Chart (for the current year, month by month)
        current_year = timezone.now().year
        monthly_payments = payments_queryset.filter(
            date_paid__year=current_year
        ).annotate(
            month=ExtractMonth('date_paid')
        ).values('month').annotate(
            # Fix: Change 0 to Decimal(0)
            total_amount=Coalesce(Sum('amount'), Decimal(0))
        ).order_by('month')
        
        # Prepare data for chart (e.g., using a list of 12 months)
        monthly_data = {item['month']: float(item['total_amount']) for item in monthly_payments}
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        # Fill in missing months with 0
        monthly_chart_data = [monthly_data.get(i + 1, 0.0) for i in range(12)]
        
        context['contributions_over_time_labels'] = month_names
        context['contributions_over_time_data'] = monthly_chart_data # Already floats

        # Top 5 Families with Most Members
        top_families = families_queryset.annotate(member_count=Count(
            'members')).order_by('-member_count')[:5]
        context['top_families_by_members'] = top_families.select_related(
            'church')

        # Top 5 Individual Contributors (using CoveredMember)
        individual_contributions_subquery = covered_members_queryset.filter(
            individual=OuterRef('pk')
        ).values('individual').annotate(
            # Fix: Change 0 to Decimal(0) and Sum('amount_allocated')
            total_allocated_amount=Coalesce(Sum('amount_allocated'), Decimal(0)) 
        ).values('total_allocated_amount')

        top_contributors = individuals_queryset.annotate(
            total_contribution=Subquery(
                individual_contributions_subquery, output_field=DecimalField())
        ).exclude(total_contribution__isnull=True).order_by('-total_contribution')[:5]
        
        context['top_individual_contributors'] = top_contributors.select_related(
            'family__church')

        # Church-wise Summary Table (always iterates through all churches)
        church_summaries = []
        for church_obj in Church.objects.all(): 
            church_families = Family.objects.filter(church=church_obj)
            church_individuals = Individual.objects.filter(family__church=church_obj)
            church_payments = Payment.objects.filter(church=church_obj)

            church_summaries.append({
                'name': church_obj.name,
                'total_families': church_families.count(),
                'total_members': church_individuals.count(),
                # Fix: Change 0 to Decimal(0)
                'total_contributions': church_payments.aggregate(total=Coalesce(Sum('amount'), Decimal(0)))['total']
            })
        context['church_summaries'] = church_summaries

        # JSON encode data for Chart.js
        context['membership_status_distribution_json'] = json.dumps(
            context['membership_status_distribution'])
        context['contributions_over_time_labels_json'] = json.dumps(
            context['contributions_over_time_labels'])
        context['contributions_over_time_data_json'] = json.dumps(
            context['contributions_over_time_data'])

        return context
