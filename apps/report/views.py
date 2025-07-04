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
# Explicitly import CharField for output_field
from django.db.models import CharField
from decimal import Decimal
from datetime import date, timedelta, datetime

# Simple helper for date calculations
from dateutil.relativedelta import relativedelta


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'report/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # --- DEBUG PRINTS START ---
        print(f"\n--- DEBUG: DashboardView Context Data Start ---")
        print(
            f"Logged in user: {self.request.user.username}, is_superuser: {self.request.user.is_superuser}")
        # --- DEBUG PRINTS END ---

        # --- Dashboard Title ---
        context['title'] = "KADAMAY Dashboard"

        # --- Church Filter Logic ---
        all_churches = Church.objects.all().order_by('name')
        context['churches'] = all_churches
        selected_church_id = self.request.GET.get('church')
        selected_church = None
        user_church_filter = None  # Filter based on user's assigned church

        # --- DEBUG PRINTS START ---
        print(
            f"URL 'church' parameter (selected_church_id): {selected_church_id}")
        # --- DEBUG PRINTS END ---

        # Determine user's assigned church if any
        if self.request.user.is_authenticated:
            try:
                user_church_assignment = UserChurch.objects.filter(
                    user=self.request.user).first()
                if user_church_assignment:
                    user_church_filter = user_church_assignment.church
                    # --- DEBUG PRINTS START ---
                    print(
                        f"User '{self.request.user.username}' is assigned to church: {user_church_filter.name} (ID: {user_church_filter.id})")
                    # --- DEBUG PRINTS END ---
                else:
                    # --- DEBUG PRINTS START ---
                    print(
                        f"User '{self.request.user.username}' has NO assigned church.")
                    # --- DEBUG PRINTS END ---
            except UserChurch.DoesNotExist:
                user_church_filter = None
                # --- DEBUG PRINTS START ---
                print("UserChurch DoesNotExist (shouldn't happen with .first())")
                # --- DEBUG PRINTS END ---

        # Apply filter based on URL parameter or user's assigned church
        if selected_church_id:
            try:
                temp_selected_church = Church.objects.get(
                    id=selected_church_id)
                # --- DEBUG PRINTS START ---
                print(
                    f"Attempting to get church from URL ID: {selected_church_id} -> Found: {temp_selected_church.name}")
                # --- DEBUG PRINTS END ---
            except Church.DoesNotExist:
                temp_selected_church = None  # Fallback if ID is invalid
                # --- DEBUG PRINTS START ---
                print(
                    f"Church with ID {selected_church_id} from URL does not exist. Temp selected church is None.")
                # --- DEBUG PRINTS END ---

            # If user is restricted to a church, ensure selected_church matches it
            if user_church_filter and temp_selected_church and temp_selected_church != user_church_filter:
                # Override if user tries to select other church
                selected_church = user_church_filter
                # --- DEBUG PRINTS START ---
                print(
                    f"URL church ID {selected_church_id} overridden by user's assigned church: {user_church_filter.name}")
                # --- DEBUG PRINTS END ---
            else:
                selected_church = temp_selected_church
                # --- DEBUG PRINTS START ---
                if selected_church:
                    print(
                        f"Selected church from URL (or matched user church): {selected_church.name}")
                # --- DEBUG PRINTS END ---
        elif user_church_filter:
            # Default to user's church if not specified
            selected_church = user_church_filter
            # --- DEBUG PRINTS START ---
            print(
                f"Defaulting to user's assigned church: {selected_church.name} (ID: {selected_church.id})")
            # --- DEBUG PRINTS END ---
        else:
            # No URL parameter, and user has no assigned church, show ALL (or handle as per your requirement)
            selected_church = None
            # --- DEBUG PRINTS START ---
            print(
                "No specific church selected in URL, and user has no assigned church. Showing ALL data.")
            # --- DEBUG PRINTS END ---

        context['selected_church'] = selected_church.id if selected_church else None
        # --- DEBUG PRINTS START ---
        print(
            f"Final active filter church (object): {selected_church} (ID: {context['selected_church']})")
        # --- DEBUG PRINTS END ---

        # --- Base Querysets based on selected_church or user's assigned church ---
        # Filter for non-cancelled payments by default for all metrics
        # Payments must be 'paid' or 'pending'
        payments_queryset = Payment.objects.filter(
            status__in=['paid', 'pending'])

        individuals_queryset = Individual.objects.all()
        families_queryset = Family.objects.all()

        # --- DEBUG PRINTS START ---
        print(
            f"Initial Individuals Queryset count: {individuals_queryset.count()}")
        print(f"Initial Families Queryset count: {families_queryset.count()}")
        # --- DEBUG PRINTS END ---

        if selected_church:
            # --- DEBUG PRINTS START ---
            print(f"Applying filter for church: {selected_church.name}")
            # --- DEBUG PRINTS END ---
            payments_queryset = payments_queryset.filter(
                individual__church=selected_church)
            individuals_queryset = individuals_queryset.filter(
                church=selected_church)
            families_queryset = families_queryset.filter(
                church=selected_church)
        else:
            # --- DEBUG PRINTS START ---
            print("No church filter applied to base querysets (showing all data).")
            # --- DEBUG PRINTS END ---

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

        # --- DEBUG PRINTS START ---
        print(
            f"Individuals Queryset count (after church filter): {individuals_queryset.count()}")
        print(
            f"Families Queryset count (after church filter): {families_queryset.count()}")
        print(
            f"Payments Queryset count (after church filter and status): {payments_queryset.count()}")
        # --- DEBUG PRINTS END ---

        # --- Dashboard Metrics ---

        context['total_contributions'] = payments_queryset.aggregate(
            total=Coalesce(Sum('amount'), Decimal(0))
        )['total']
        # --- DEBUG PRINTS START ---
        print(
            f"Context['total_contributions']: {context['total_contributions']}")
        # --- DEBUG PRINTS END ---

        # Count of non-cancelled payments
        context['total_payments'] = payments_queryset.count()
        # --- DEBUG PRINTS START ---
        print(f"Context['total_payments']: {context['total_payments']}")
        # --- DEBUG PRINTS END ---

        context['total_individuals'] = individuals_queryset.count()
        # Alias for clarity in template
        context['total_members'] = context['total_individuals']
        # --- DEBUG PRINTS START ---
        print(
            f"Context['total_individuals'] (sent to template): {context['total_individuals']}")
        # --- DEBUG PRINTS END ---

        context['total_families'] = families_queryset.count()
        # --- DEBUG PRINTS START ---
        print(
            f"Context['total_families'] (sent to template): {context['total_families']}")
        # --- DEBUG PRINTS END ---

        # Total Registered Churches (show only the user's church or all if admin/no church assigned)
        if selected_church:
            context['total_churches'] = 1
        # Only show all churches count if not restricted by user_church AND is superuser
        elif not user_church_filter and self.request.user.is_superuser:
            context['total_churches'] = Church.objects.count()
        elif user_church_filter:  # User is restricted but no specific church selected, show only their church
            context['total_churches'] = 1
        # Default for users without assigned church and no filter (not superuser), should ideally show all or 0 if no permissions
        else:
            context['total_churches'] = Church.objects.count()
        # --- DEBUG PRINTS START ---
        print(
            f"Context['total_churches'] (sent to template): {context['total_churches']}")
        # --- DEBUG PRINTS END ---

        # Active members are individuals who have made at least one non-cancelled payment
        context['active_members_count'] = payments_queryset.values(
            'individual').distinct().count()
        # --- DEBUG PRINTS START ---
        print(
            f"Context['active_members_count']: {context['active_members_count']}")
        # --- DEBUG PRINTS END ---

        # --- Recent Payments ---
        context['recent_payments'] = payments_queryset.order_by(
            '-date_paid')[:10]
        # --- DEBUG PRINTS START ---
        print(
            f"Context['recent_payments'] count: {context['recent_payments'].count()}")
        # --- DEBUG PRINTS END ---

        # --- Top Churches by Contributions ---
        if not selected_church:  # Only show this table if viewing ALL churches
            context['top_churches_by_contributions'] = payments_queryset.values('individual__church__name').annotate(
                total_amount=Coalesce(Sum('amount'), Decimal(0))
            ).order_by('-total_amount')[:5]
        else:
            # Don't show if filtered to one church
            context['top_churches_by_contributions'] = []
        # --- DEBUG PRINTS START ---
        print(
            f"Context['top_churches_by_contributions'] count: {len(context['top_churches_by_contributions'])}")
        # --- DEBUG PRINTS END ---

        # --- Top Contribution Types ---
        context['top_contribution_types'] = payments_queryset.values('contribution_type__name').annotate(
            total_amount=Coalesce(Sum('amount'), Decimal(0))
        ).order_by('-total_amount')[:5]
        # --- DEBUG PRINTS START ---
        print(
            f"Context['top_contribution_types'] count: {len(context['top_contribution_types'])}")
        # --- DEBUG PRINTS END ---

        # --- Membership Status Distribution (For your JSON.parse) ---
        # Define all possible statuses to ensure consistent labels in chart, even if count is 0
        # Updated to reflect only choices in Individual model for `membership_status`
        all_possible_statuses = ['Active', 'Inactive', 'Pending']

        # Aggregate counts, ensuring 'None' or empty statuses are grouped as 'Unknown/Not Set'
        membership_status_raw_data = individuals_queryset.annotate(
            # Coalesce handles None values, replacing them with 'UNKNOWN'
            actual_status=Coalesce(F('membership_status'), Value(
                'UNKNOWN', output_field=CharField()))
        ).values('actual_status').annotate(
            count=Count('id')
        ).order_by('actual_status')

        membership_status_chart_data = {
            # Added 'UNKNOWN' here too
            status: 0 for status in all_possible_statuses + ['UNKNOWN']}
        for item in membership_status_raw_data:
            status_name = item['actual_status']
            # Convert status name from DB (e.g., 'ACTIVE') to display (e.g., 'Active')
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
            # --- DEBUG PRINTS START ---
            print(
                f"Membership Status JSON (first 100 chars): {context['membership_status_distribution_json'][:100]}...")
            # --- DEBUG PRINTS END ---
        except Exception as e:
            # --- DEBUG PRINTS START ---
            print(
                f"ERROR: Could not serialize membership status data to JSON: {e}")
            # --- DEBUG PRINTS END ---
            context['membership_status_distribution_json'] = json.dumps({})

        # --- Monthly Contributions Trend (Last 6 months using TruncMonth) ---
        today = date.today()
        # Calculate the start date for the last 6 months (e.g., if today is Jun 24, 2025, it starts from Jan 1, 2025)
        # Using relativedelta for more accurate month calculations
        # This gets the 1st day of 6 months ago
        start_date_for_chart = today.replace(day=1) - relativedelta(months=5)

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
        # Loop to cover 6 months: start_date_for_chart up to and including the current month
        for _ in range(6):  # Loop exactly 6 times for 6 months
            month_label = current_month_iter.strftime(
                '%b %Y')  # e.g., "Jan 2025"
            month_key = current_month_iter.strftime('%Y-%m')  # e.g., "2025-01"

            contributions_over_time_labels.append(month_label)
            # Get amount from dict, default to 0.00 if no payments for that month
            contributions_over_time_data.append(
                contributions_dict.get(month_key, 0.00))

            # Move to next month
            current_month_iter += relativedelta(months=1)

        context['contributions_over_time_labels_json'] = json.dumps(
            contributions_over_time_labels)
        context['contributions_over_time_data_json'] = json.dumps(
            contributions_over_time_data)
        # --- DEBUG PRINTS START ---
        print(
            f"Contributions Over Time Labels JSON (first 100 chars): {context['contributions_over_time_labels_json'][:100]}...")
        print(
            f"Contributions Over Time Data JSON (first 100 chars): {context['contributions_over_time_data_json'][:100]}...")
        # --- DEBUG PRINTS END ---

        # --- Top 5 Families with Most Members ---
        context['top_families_by_members'] = families_queryset.annotate(
            # Assuming 'members' is related_name from Family to Individual
            member_count=Coalesce(Count('members', distinct=True), 0)
        ).order_by('-member_count')[:5].select_related('church')
        # --- DEBUG PRINTS START ---
        print(
            f"Top Families by Members Queryset count (after annotation): {context['top_families_by_members'].count()}")
        for family_entry in context['top_families_by_members']:
            print(
                f"  Family: {family_entry.family_name}, Members: {family_entry.member_count}")
        # --- DEBUG PRINTS END ---

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
            contributor['family'] = {'family_name': contributor.get(
                'individual__family__family_name')}
            contributor['church'] = {
                'name': contributor.get('individual__church__name')}
        # --- DEBUG PRINTS START ---
        print(
            f"Top Individual Contributors count: {len(context['top_individual_contributors'])}")
        # --- DEBUG PRINTS END ---

        # --- Church-wise Summary Table ---
        if not selected_church:
            context['church_summaries'] = Church.objects.annotate(
                total_families=Coalesce(Count('families', distinct=True), 0),
                total_members=Coalesce(Count('individuals', distinct=True), 0),
                # Filter for 'paid' or 'pending' payments for consistency
                total_contributions=Coalesce(
                    Sum('individuals__payments_as_payer__amount', # <--- CORRECTED LINE
                        filter=Q(individuals__payments_as_payer__status__in=['paid', 'pending'])), Decimal(0)) # <--- CORRECTED LINE
            ).order_by('name')
            # --- DEBUG PRINTS START ---
            print(
                f"Church Summaries (all churches) count: {context['church_summaries'].count()}")
            for church_sum in context['church_summaries']:
                print(
                    f"  Church: {church_sum.name}, Families: {church_sum.total_families}, Members: {church_sum.total_members}")
            # --- DEBUG PRINTS END ---
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
            # Pass as a list for template loop
            context['church_summaries'] = [church_summary_data]
            # --- DEBUG PRINTS START ---
            print(
                f"Church Summaries (selected church) count: {len(context['church_summaries'])}")
            print(f"  Selected Church Summary: {church_summary_data}")
            # --- DEBUG PRINTS END ---

        # --- DEBUG PRINTS END ---
        print(f"--- DEBUG: DashboardView Context Data End ---")
        return context