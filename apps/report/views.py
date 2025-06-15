from django.views.generic import View
from django.shortcuts import render
from django.db.models import Count, Sum
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.church.models import Church
from apps.family.models import Family
from apps.individual.models import Individual
from apps.payment.models import Payment
from django.utils import timezone
from django.db.models.functions import ExtractMonth, ExtractYear
import json  # Important: Import json for data serialization


class DashboardView(LoginRequiredMixin, View):
    template_name = 'report/dashboard.html'

    def get(self, request, *args, **kwargs):
        selected_church_id = request.GET.get('church')

        # Determine which churches to include based on user type and filter
        if request.user.is_superuser:
            all_available_churches = Church.objects.all().order_by('name')
        else:
            # Assuming UserChurch model assigns a church to a user
            user_church_assignment = request.user.assigned_church.first()
            if user_church_assignment:
                all_available_churches = Church.objects.filter(
                    id=user_church_assignment.church.id).order_by('name')
            else:
                all_available_churches = Church.objects.none()  # No churches assigned

        # Apply the filter if a specific church is selected
        if selected_church_id:
            try:
                churches_to_display = all_available_churches.filter(
                    id=int(selected_church_id))
            except ValueError:
                churches_to_display = all_available_churches  # Invalid ID, show all available
        else:
            churches_to_display = all_available_churches

        church_ids_to_display = [church.id for church in churches_to_display]

        # Querysets based on the churches selected/filtered
        individual_queryset = Individual.objects.filter(
            family__church__id__in=church_ids_to_display)
        family_queryset = Family.objects.filter(
            church__id__in=church_ids_to_display)
        payment_queryset = Payment.objects.filter(
            individual__family__church__id__in=church_ids_to_display)

        # --- Dashboard Stats ---
        total_churches = churches_to_display.count()
        total_families = family_queryset.count()
        total_members = individual_queryset.count()

        active_members_count = individual_queryset.filter(
            is_active_member=True, is_alive=True).count()
        inactive_deceased = individual_queryset.filter(is_alive=False).count()
        inactive_alive = individual_queryset.filter(
            is_active_member=False, is_alive=True).count()

        total_payments = payment_queryset.aggregate(
            total_amount=Sum('amount'))['total_amount'] or 0
        recent_members = individual_queryset.order_by('-date_added')[:5]

        # --- Data for "Families per Church" Chart ---
        family_counts_per_church = churches_to_display.annotate(
            num_families=Count('families')
        ).values('name', 'num_families').order_by('name')

        church_names = [item['name'] for item in family_counts_per_church]
        family_counts_data = [item['num_families']
                              for item in family_counts_per_church]

        # --- Data for "Monthly Contributions" Chart ---
        monthly_contributions = {}
        today = timezone.now()

        # Initialize monthly_contributions for the last 12 months with 0
        for i in range(11, -1, -1):  # Iterate from 11 down to 0 to get chronological order
            month_date = (today - timezone.timedelta(days=30 * i)
                          ).replace(day=1)
            month_str = month_date.strftime('%Y-%m')  # e.g., "2024-01"
            month_label = month_date.strftime('%b %Y')  # e.g., "Jan 2024"
            monthly_contributions[month_str] = {
                'label': month_label, 'total_amount': 0}

        # Aggregate payments by month
        # Approximate 12 months ago
        twelve_months_ago = today - timezone.timedelta(days=365)

        payments_by_month = payment_queryset.filter(
            date_paid__gte=twelve_months_ago
        ).annotate(
            year=ExtractYear('date_paid'),
            month=ExtractMonth('date_paid')
        ).values('year', 'month').annotate(
            total=Sum('amount')
        ).order_by('year', 'month')

        for entry in payments_by_month:
            # Format YYYY-MM
            month_key = f"{entry['year']}-{entry['month']:02d}"
            if month_key in monthly_contributions:
                monthly_contributions[month_key]['total_amount'] = float(
                    entry['total'])  # Ensure float for JS

        # Extract labels and data in correct chronological order
        months_labels = [monthly_contributions[key]['label']
                         for key in sorted(monthly_contributions.keys())]
        contributions_data = [monthly_contributions[key]['total_amount']
                              for key in sorted(monthly_contributions.keys())]

        context = {
            'total_churches': total_churches,
            'total_families': total_families,
            'total_members': total_members,
            'active_members': active_members_count,
            'inactive_deceased': inactive_deceased,
            'inactive_alive': inactive_alive,
            'total_payments': total_payments,
            'recent_members': recent_members,
            'title': 'System Dashboard',

            # Pass all available churches for the filter dropdown
            'churches': all_available_churches,
            # Pass the selected ID back to the template
            'selected_church': selected_church_id,

            # Data for Charts (JSON serialized for JavaScript)
            'church_names': json.dumps(church_names),
            'family_counts': json.dumps(family_counts_data),
            'months': json.dumps(months_labels),
            'contributions': json.dumps(contributions_data),
        }
        return render(request, self.template_name, context)
