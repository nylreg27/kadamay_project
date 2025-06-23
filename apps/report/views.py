# apps/report/views.py

import json
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.payment.models import Payment
from apps.individual.models import Individual
from apps.church.models import Church
from apps.family.models import Family
from apps.account.models import Profile, UserChurch 

# Import Value and CharField here
from django.db.models import Sum, Count, F, Q, Value
from django.db.models.functions import Coalesce, TruncMonth 
from django.db.models import CharField # Explicitly import CharField for output_field
from decimal import Decimal
from datetime import date, timedelta, datetime


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'report/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # --- Dashboard Title ---
        context['title'] = "KADAMAY Dashboard"

        # --- Church Filter Logic ---
        all_churches = Church.objects.all().order_by('name')
        context['churches'] = all_churches
        selected_church_id = self.request.GET.get('church')
        selected_church = None
        user_church_filter = None  # Filter based on user's assigned church

        # Determine user's assigned church if any
        if self.request.user.is_authenticated:
            try:
                user_church_assignment = UserChurch.objects.filter(user=self.request.user).first()
                if user_church_assignment:
                    user_church_filter = user_church_assignment.church
            except UserChurch.DoesNotExist:
                user_church_filter = None

        # Apply filter based on URL parameter or user's assigned church
        if selected_church_id:
            try:
                selected_church = Church.objects.get(id=selected_church_id)
            except Church.DoesNotExist:
                selected_church = None  # Fallback if ID is invalid
            # If user is restricted to a church, ensure selected_church matches it
            if user_church_filter and selected_church and selected_church != user_church_filter:
                # Override if user tries to select other church
                selected_church = user_church_filter
        elif user_church_filter:
            # Default to user's church if not specified
            selected_church = user_church_filter

        context['selected_church'] = selected_church.id if selected_church else None

        # --- Base Querysets based on selected_church or user's assigned church ---
        # Filter for non-cancelled payments by default for all metrics
        # FIXED: Changed is_cancelled=False to status__in=['paid', 'pending']
        payments_queryset = Payment.objects.filter(status__in=['paid', 'pending']) 
        
        individuals_queryset = Individual.objects.all()
        families_queryset = Family.objects.all()

        if selected_church:
            payments_queryset = payments_queryset.filter(
                individual__church=selected_church)
            individuals_queryset = individuals_queryset.filter(
                church=selected_church)
            families_queryset = families_queryset.filter(
                church=selected_church)

        # Optimize with select_related and prefetch_related for efficient fetching
        payments_queryset = payments_queryset.select_related(
            'individual__church',
            'contribution_type',
            'collected_by'
        ).prefetch_related(
            'covered_members'
        )
        individuals_queryset = individuals_queryset.select_related(
            'family', 'church')
        families_queryset = families_queryset.select_related('church')

        # --- Dashboard Metrics ---

        context['total_contributions'] = payments_queryset.aggregate(
            total=Coalesce(Sum('amount'), Decimal(0))
        )['total']

        context['total_payments'] = payments_queryset.count() # Count of non-cancelled payments

        context['total_individuals'] = individuals_queryset.count()
        context['total_members'] = context['total_individuals'] # Alias for clarity in template

        context['total_families'] = families_queryset.count()

        # Total Registered Churches (show only the user's church or all if admin/no church assigned)
        if selected_church:
            context['total_churches'] = 1
        elif not user_church_filter:  # Only show all churches count if not restricted by user_church
            context['total_churches'] = Church.objects.count()
        else:  # User is restricted but no specific church selected, show only their church
            context['total_churches'] = 1

        # Active members are individuals who have made at least one non-cancelled payment
        context['active_members_count'] = payments_queryset.values('individual').distinct().count()

        # --- Recent Payments ---
        context['recent_payments'] = payments_queryset.order_by('-date_paid')[:10]

        # --- Top Churches by Contributions ---
        if not selected_church:  # Only show this table if viewing ALL churches
            context['top_churches_by_contributions'] = payments_queryset.values('individual__church__name').annotate(
                total_amount=Coalesce(Sum('amount'), Decimal(0))
            ).order_by('-total_amount')[:5]
        else:
            context['top_churches_by_contributions'] = [] # Don't show if filtered to one church

        # --- Top Contribution Types ---
        context['top_contribution_types'] = payments_queryset.values('contribution_type__name').annotate(
            total_amount=Coalesce(Sum('amount'), Decimal(0))
        ).order_by('-total_amount')[:5]

        # --- Membership Status Distribution (For your JSON.parse) ---
        # Define all possible statuses to ensure consistent labels in chart, even if count is 0
        # Updated to reflect only choices in Individual model for `membership_status` 
        all_possible_statuses = ['Active', 'Inactive', 'Pending'] 

        # Aggregate counts, ensuring 'None' or empty statuses are grouped as 'Unknown/Not Set'
        membership_status_raw_data = individuals_queryset.annotate(
            # Coalesce handles None values, replacing them with 'Unknown/Not Set' - keep this as it handles potentially null statuses
            # CORRECTED: Wrap 'UNKNOWN' in Value() and add output_field
            actual_status=Coalesce(F('membership_status'), Value('UNKNOWN', output_field=CharField())) 
        ).values('actual_status').annotate(
            count=Count('id')
        ).order_by('actual_status')

        membership_status_chart_data = {status: 0 for status in all_possible_statuses + ['UNKNOWN']} # Added 'UNKNOWN' here too
        for item in membership_status_raw_data:
            status_name = item['actual_status']
            # Convert status name from DB (e.g., 'ACTIVE') to display (e.g., 'Active') if needed
            # For now, assuming chart.js can handle 'ACTIVE', 'INACTIVE', 'PENDING'
            if status_name == 'ACTIVE':
                status_name = 'Active'
            elif status_name == 'INACTIVE':
                status_name = 'Inactive'
            elif status_name == 'PENDING':
                status_name = 'Pending'
            # else: status_name remains 'UNKNOWN'

            membership_status_chart_data[status_name] = item['count']

        try:
            context['membership_status_distribution_json'] = json.dumps(
                membership_status_chart_data)
        except Exception as e:
            print(f"ERROR: Could not serialize membership status data to JSON: {e}")
            context['membership_status_distribution_json'] = json.dumps({})


        # --- Monthly Contributions Trend (Last 6 months using TruncMonth) ---
        today = date.today()
        # Calculate the start date for the last 6 months (inclusive of current month)
        # e.g., if today is 2025-06-23, start_date is 2025-01-01
        start_date_for_chart = (today - timedelta(days=5 * 30)).replace(day=1) # Start of 6 months ago

        monthly_contributions_raw = payments_queryset.filter(
            date_paid__gte=start_date_for_chart
        ).annotate(
            month=TruncMonth('date_paid')
        ).values('month').annotate(
            total_amount=Coalesce(Sum('amount'), Decimal(0))
        ).order_by('month')

        # Create a dictionary for quick lookup of aggregated amounts
        contributions_dict = {
            entry['month'].strftime('%Y-%m'): float(entry['total_amount'])
            for entry in monthly_contributions_raw
        }

        # Generate labels and data for the last 6 months, ensuring all months are present
        contributions_over_time_labels = []
        contributions_over_time_data = []

        current_month_iter = start_date_for_chart
        # Loop to cover 6 months: start_date_for_chart up to (but not including) next month after today
        while current_month_iter <= today.replace(day=1):
            month_label = current_month_iter.strftime('%b %Y') # e.g., "Jan 2025"
            month_key = current_month_iter.strftime('%Y-%m') # e.g., "2025-01"

            contributions_over_time_labels.append(month_label)
            # Get amount from dict, default to 0.00 if no payments for that month
            contributions_over_time_data.append(contributions_dict.get(month_key, 0.00))

            # Move to next month
            if current_month_iter.month == 12:
                current_month_iter = current_month_iter.replace(year=current_month_iter.year + 1, month=1)
            else:
                current_month_iter = current_month_iter.replace(month=current_month_iter.month + 1)
            
        # Ensure we don't go beyond 6 months or current month, slicing to max 6 entries
        contributions_over_time_labels = contributions_over_time_labels[-6:]
        contributions_over_time_data = contributions_over_time_data[-6:]


        context['contributions_over_time_labels_json'] = json.dumps(
            contributions_over_time_labels)
        context['contributions_over_time_data_json'] = json.dumps(
            contributions_over_time_data)

        # --- Top 5 Families with Most Members ---
        context['top_families_by_members'] = families_queryset.annotate(
            member_count=Coalesce(Count('members', distinct=True), 0) # Assuming 'members' is related_name from Family to Individual
        ).order_by('-member_count')[:5].select_related('church')

        # --- Top 5 Individual Contributors ---
        # Note: payments_queryset already filters for non-cancelled payments
        context['top_individual_contributors'] = payments_queryset.values(
            'individual__id',
            'individual__given_name',
            'individual__surname',
            'individual__middle_name',
            'individual__suffix_name',
            # 'individual__profile_picture', # Uncomment if Individual model has this field
            'individual__family__family_name',
            'individual__church__name',
        ).annotate(
            total_contribution=Coalesce(Sum('amount'), Decimal(0))
        ).order_by('-total_contribution')[:5]

        # Add full_name attribute for easier display in template
        for contributor in context['top_individual_contributors']:
            full_name_parts = [
                contributor.get('individual__given_name', ''),
                contributor.get('individual__middle_name', ''),
                contributor.get('individual__surname', ''),
                contributor.get('individual__suffix_name', '')
            ]
            contributor['full_name'] = ' '.join(filter(None, full_name_parts))
            # contributor['profile_picture'] = contributor.get('individual__profile_picture') # Uncomment if Individual has profile_picture
            contributor['family'] = {'family_name': contributor.get('individual__family__family_name')}
            contributor['church'] = {'name': contributor.get('individual__church__name')}

        # --- Church-wise Summary Table ---
        if not selected_church:
            context['church_summaries'] = Church.objects.annotate(
                total_families=Coalesce(Count('families', distinct=True), 0),
                total_members=Coalesce(Count('individuals', distinct=True), 0),
                # FIXED: Changed is_cancelled=False to status='cancelled' for payments filter
                total_contributions=Coalesce(
                    Sum('individuals__payments_made__amount', filter=~Q(individuals__payments_made__status='cancelled')), Decimal(0)) 
            ).order_by('name')
        else:
            # If a specific church is selected, create a summary just for that church
            # We already have filtered querysets, just aggregate their counts/sums
            church_summary_data = {
                'name': selected_church.name,
                # 'logo': selected_church.logo.url if selected_church.logo else None, # Uncomment if Church model has a logo field
                'total_families': families_queryset.count(),
                'total_members': individuals_queryset.count(),
                'total_contributions': payments_queryset.aggregate(total=Coalesce(Sum('amount'), Decimal(0)))['total'],
            }
            context['church_summaries'] = [church_summary_data] # Pass as a list for template loop

        return context