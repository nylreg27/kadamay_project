# apps/report/views.py

from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.payment.models import Payment  # Import the Payment model
from apps.individual.models import Individual  # Import Individual
from apps.church.models import Church  # Import Church
from django.db.models import Sum, Count  # For aggregations
from django.db.models.functions import Coalesce  # To handle null sums as 0
from decimal import Decimal  # For Decimal(0)
from datetime import date, timedelta  # For date calculations

# Optional: Import UserChurch and Profile if needed for specific filtering/display
# from apps.account.models import UserChurch, Profile


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'report/dashboard.html'  # Make sure this path is correct

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # --- Base Queryset for Payments ---
        payments_queryset = Payment.objects.all()

        # You might want to filter payments based on the user's church if applicable
        # if hasattr(self.request.user, 'user_church') and self.request.user.user_church.church:
        #     payments_queryset = payments_queryset.filter(church=self.request.user.user_church.church)

        # Optimize with select_related and prefetch_related if you need related data
        payments_queryset = payments_queryset.select_related(
            'individual', 'church', 'contribution_type', 'collected_by'
        ).prefetch_related(
            'covered_members'
        )

        # --- Dashboard Metrics ---

        # Total Contributions
        context['total_contributions'] = payments_queryset.aggregate(
            # Corrected: 'amount' to 'amount_paid'
            total=Coalesce(Sum('amount_paid'), Decimal(0))
        )['total']

        # Total Number of Payments
        context['total_payments'] = payments_queryset.count()

        # Total Registered Individuals
        context['total_individuals'] = Individual.objects.count()

        # Total Registered Churches
        context['total_churches'] = Church.objects.count()

        # Number of Active Members (Example: individuals with at least one payment)
        # This might need refinement based on your definition of "active member"
        context['active_members_count'] = Individual.objects.filter(
            payments_made__isnull=False
        ).distinct().count()

        # --- Recent Payments (Example) ---
        context['recent_payments'] = payments_queryset.order_by(
            '-date_paid')[:10]

        # --- Top Churches by Contributions (Example) ---
        context['top_churches_by_contributions'] = payments_queryset.values('church__name').annotate(
            # Corrected: 'amount' to 'amount_paid'
            total_amount=Coalesce(Sum('amount_paid'), Decimal(0))
        ).order_by('-total_amount')[:5]

        # --- Top Contribution Types (Example) ---
        context['top_contribution_types'] = payments_queryset.values('contribution_type__name').annotate(
            # Corrected: 'amount' to 'amount_paid'
            total_amount=Coalesce(Sum('amount_paid'), Decimal(0))
        ).order_by('-total_amount')[:5]

        # --- Payments by Status ---
        context['payments_by_status'] = payments_queryset.values('status').annotate(
            count=Count('id'),
            # Corrected: 'amount' to 'amount_paid'
            total_amount=Coalesce(Sum('amount_paid'), Decimal(0))
        )

        # --- Monthly Contributions Trend (Last 6 months) ---
        monthly_contributions = {}
        today = date.today()
        for i in range(6):  # Last 6 months including current month
            month = (today.replace(day=1) - timedelta(days=1)
                     ).replace(day=1) if i > 0 else today.replace(day=1)

            # Filter payments for the current month in the loop
            month_payments = payments_queryset.filter(
                date_paid__year=month.year,
                date_paid__month=month.month
            )
            total_for_month = month_payments.aggregate(
                # Corrected: 'amount' to 'amount_paid'
                total=Coalesce(Sum('amount_paid'), Decimal(0))
            )['total']

            # Convert Decimal to float for JSON/Chart compatibility
            monthly_contributions[month.strftime(
                '%Y-%m')] = float(total_for_month)

            # Move to the previous month for the next iteration
            today = month - timedelta(days=1)

        # Reverse to get chronological order for charts if needed
        context['monthly_contributions_data'] = dict(
            sorted(monthly_contributions.items()))

        return context
