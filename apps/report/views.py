# apps/report/views.py

import json
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.payment.models import Payment
from apps.individual.models import Individual
from apps.church.models import Church
from apps.family.models import Family
from apps.account.models import Profile, UserChurch

from django.db.models import Sum, Count, F, Q
from django.db.models.functions import Coalesce
from decimal import Decimal
# Ensure datetime is imported for strptime
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
                user_church_assignment = UserChurch.objects.filter(
                    user=self.request.user).first()
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
        payments_queryset = Payment.objects.all()
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
        # Add select_related for families and individuals if needed for other queries
        individuals_queryset = individuals_queryset.select_related(
            'family', 'church')
        families_queryset = families_queryset.select_related('church')

        # --- Dashboard Metrics ---

        context['total_contributions'] = payments_queryset.aggregate(
            total=Coalesce(Sum('amount'), Decimal(0))
        )['total']

        context['total_payments'] = payments_queryset.count()

        # This is 'Total Members'
        context['total_individuals'] = individuals_queryset.count()
        # Alias for clarity in template
        context['total_members'] = context['total_individuals']

        # <--- Total Families count
        context['total_families'] = families_queryset.count()

        # Total Registered Churches (show only the user's church or all if admin/no church assigned)
        # The church filter handles this, so total_churches will be 1 if filtered.
        # This context variable should ideally reflect the count *after* any filters applied.
        if selected_church:
            context['total_churches'] = 1
        elif not user_church_filter:  # Only show all churches count if not restricted by user_church
            context['total_churches'] = Church.objects.count()
        else:  # User is restricted but no specific church selected, show only their church
            context['total_churches'] = 1

        context['active_members_count'] = payments_queryset.values(
            'individual').distinct().count()

        # --- Recent Payments (Example) ---
        context['recent_payments'] = payments_queryset.order_by(
            '-date_paid')[:10]

        # --- Top Churches by Contributions (Example) ---
        # Only aggregate by church if not already filtered by a specific church
        if not selected_church:  # Only show this table if viewing ALL churches
            context['top_churches_by_contributions'] = payments_queryset.values('individual__church__name').annotate(
                total_amount=Coalesce(Sum('amount'), Decimal(0))
            ).order_by('-total_amount')[:5]
        else:
            # Don't show if filtered to one church
            context['top_churches_by_contributions'] = []

        # --- Top Contribution Types (Example) ---
        context['top_contribution_types'] = payments_queryset.values('contribution_type__name').annotate(
            total_amount=Coalesce(Sum('amount'), Decimal(0))
        ).order_by('-total_amount')[:5]

        # --- Payments by Status ---
        # Assuming 'status' is a field on the Payment model based on your earlier traceback (though not directly in Individual model)
        context['payments_by_status'] = payments_queryset.values('status').annotate(
            count=Count('id'),
            total_amount=Coalesce(Sum('amount'), Decimal(0))
        )

        # --- Membership Status Distribution (For your JSON.parse) ---
        membership_status_raw_data = individuals_queryset.values('membership_status').annotate(
            count=Count('id')
            # Corrected: Used 'membership_status' as per your model
        ).order_by('membership_status')

        membership_status_chart_data = {}
        # Define a consistent order for statuses if you have specific ones
        # Example statuses: 'Active', 'Inactive', 'Pending', 'Deceased'
        # Fallback for 'None' or empty string
        for item in membership_status_raw_data:
            # Corrected: Used 'membership_status' as the key to access the value
            status_name = item['membership_status'] if item['membership_status'] else 'Unknown/Not Set'
            membership_status_chart_data[status_name] = item['count']

        try:
            context['membership_status_distribution_json'] = json.dumps(
                membership_status_chart_data)
        except Exception as e:
            print(
                f"ERROR: Could not serialize membership status data to JSON: {e}")
            context['membership_status_distribution_json'] = json.dumps({})

        # --- Monthly Contributions Trend (Last 6 months) ---
        monthly_contributions_data = {}
        monthly_labels = []
        monthly_amounts = []

        # Start from the first day of current month
        current_date_loop = date.today().replace(day=1)

        for _ in range(6):  # Loop for the last 6 months (current month + 5 previous)
            month_payments = payments_queryset.filter(
                date_paid__year=current_date_loop.year,
                date_paid__month=current_date_loop.month
            )
            total_for_month = month_payments.aggregate(
                total=Coalesce(Sum('amount'), Decimal(0))
            )['total']

            month_label = current_date_loop.strftime(
                '%b %Y')  # e.g., 'Jun 2024'
            monthly_contributions_data[month_label] = float(total_for_month)

            # Move to the first day of the previous month
            if current_date_loop.month == 1:
                current_date_loop = current_date_loop.replace(
                    year=current_date_loop.year - 1, month=12)
            else:
                current_date_loop = current_date_loop.replace(
                    month=current_date_loop.month - 1)

        # Sort the data by month (oldest to newest) for charting
        # We collected them in reverse, so sort by date value
        sorted_monthly_data = sorted(monthly_contributions_data.items(),
                                     key=lambda item: datetime.strptime(item[0], '%b %Y'))

        for label, amount in sorted_monthly_data:
            monthly_labels.append(label)
            monthly_amounts.append(amount)

        context['contributions_over_time_labels_json'] = json.dumps(
            monthly_labels)
        context['contributions_over_time_data_json'] = json.dumps(
            monthly_amounts)

        # --- Top 5 Families with Most Members ---
        context['top_families_by_members'] = families_queryset.annotate(
            # Corrected: Used 'members' to count related individuals
            member_count=Count('members')
        ).order_by('-member_count')[:5].select_related('church')

        # --- Top 5 Individual Contributors ---
        context['top_individual_contributors'] = payments_queryset.values(
            'individual__id',
            'individual__given_name',  # Corrected: 'given_name' as per model
            'individual__surname',  # Corrected: 'surname' as per model
            'individual__middle_name',
            'individual__suffix_name',  # Corrected: 'suffix_name' as per model
            # 'individual__profile_picture', # If this field exists, keep it. Not in your provided Individual model schema.
            'individual__family__family_name',
            'individual__church__name',
        ).annotate(
            total_contribution=Coalesce(Sum('amount'), Decimal(0))
        ).order_by('-total_contribution')[:5]

        # Add full_name attribute for easier display in template
        for contributor in context['top_individual_contributors']:
            full_name_parts = [
                # Corrected: Use 'given_name'
                contributor.get('individual__given_name', ''),
                contributor.get('individual__middle_name', ''),
                # Corrected: Use 'surname'
                contributor.get('individual__surname', ''),
                # Corrected: Use 'suffix_name'
                contributor.get('individual__suffix_name', '')
            ]
            contributor['full_name'] = ' '.join(filter(None, full_name_parts))
            # contributor['profile_picture'] = contributor.get( # Uncomment if profile_picture is added to Individual model
            #     'individual__profile_picture')
            contributor['family'] = {'family_name': contributor.get(
                'individual__family__family_name')}
            contributor['church'] = {'name': contributor.get(
                'individual__church__name')}

        # --- Church-wise Summary Table ---
        # This aggregation is only useful if not filtering by a single church
        if not selected_church:
            context['church_summaries'] = Church.objects.annotate(
                total_families=Coalesce(Count('families', distinct=True), 0),
                total_members=Coalesce(Count('individuals', distinct=True), 0),
                total_contributions=Coalesce(
                    Sum('individuals__payments_made__amount'), Decimal(0))
            ).order_by('name')
        else:
            # If a specific church is selected, create a summary just for that church
            # or pass an empty list if you prefer not to show this table at all when filtered
            church_summary_data = {
                'name': selected_church.name,
                # 'logo': selected_church.logo, # Uncomment if Church model has a logo field. Not in current context.
                'total_families': families_queryset.count(),
                'total_members': individuals_queryset.count(),
                'total_contributions': payments_queryset.aggregate(total=Coalesce(Sum('amount'), Decimal(0)))['total'],
            }
            # Pass as a list for template loop
            context['church_summaries'] = [church_summary_data]

        return context
