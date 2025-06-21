# apps/report/views.py

from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.payment.models import Payment
from apps.individual.models import Individual
from apps.church.models import Church
# IMPORT YOUR ACTUAL MODELS
from apps.account.models import Profile, UserChurch  # Corrected import

from django.db.models import Sum, Count
from django.db.models.functions import Coalesce
from decimal import Decimal
from datetime import date, timedelta


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'report/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # --- Get the current user's church from UserChurch model ---
        user_church = None
        if self.request.user.is_authenticated:
            try:
                # Access the assigned_church through the user.
                # Use .first() in case a user is somehow assigned to multiple churches
                # or if the relationship is not always OneToOne
                user_church_assignment = self.request.user.assigned_church.first()
                if user_church_assignment:
                    user_church = user_church_assignment.church
            except UserChurch.DoesNotExist:
                user_church = None  # User has no church assigned

        # --- Base Queryset for Payments ---
        payments_queryset = Payment.objects.all()

        # If the user is linked to a specific church, filter payments by that church
        if user_church:
            payments_queryset = payments_queryset.filter(
                individual__church=user_church)

        # Optimize with select_related and prefetch_related for efficient fetching
        payments_queryset = payments_queryset.select_related(
            'individual__church',  # Follow the relationship: Payment -> Individual -> Church
            'contribution_type',
            'collected_by'
        ).prefetch_related(
            'covered_members'
        )

        # --- Dashboard Metrics ---

        context['total_contributions'] = payments_queryset.aggregate(
            total=Coalesce(Sum('amount'), Decimal(0))
        )['total']

        context['total_payments'] = payments_queryset.count()

        # Total Registered Individuals (filtered by user's church if applicable)
        individuals_queryset = Individual.objects.all()
        if user_church:
            individuals_queryset = individuals_queryset.filter(
                church=user_church)
        context['total_individuals'] = individuals_queryset.count()

        # Total Registered Churches (show only the user's church or all if admin)
        if user_church:
            context['total_churches'] = 1  # Only the assigned church
        else:
            context['total_churches'] = Church.objects.count()

        # Number of Active Members (Individuals with at least one payment in the filtered queryset)
        context['active_members_count'] = payments_queryset.values(
            'individual').distinct().count()

        # --- Recent Payments (Example) ---
        context['recent_payments'] = payments_queryset.order_by(
            '-date_paid')[:10]

        # --- Top Churches by Contributions (Example) ---
        context['top_churches_by_contributions'] = payments_queryset.values('individual__church__name').annotate(
            total_amount=Coalesce(Sum('amount'), Decimal(0))
        ).order_by('-total_amount')[:5]

        # --- Top Contribution Types (Example) ---
        context['top_contribution_types'] = payments_queryset.values('contribution_type__name').annotate(
            total_amount=Coalesce(Sum('amount'), Decimal(0))
        ).order_by('-total_amount')[:5]

        # --- Payments by Status ---
        context['payments_by_status'] = payments_queryset.values('status').annotate(
            count=Count('id'),
            total_amount=Coalesce(Sum('amount'), Decimal(0))
        )

        # --- Monthly Contributions Trend (Last 6 months) ---
        monthly_contributions = {}
        today = date.today()
        for i in range(6):
            current_month_start = today.replace(day=1)

            month_payments = payments_queryset.filter(
                date_paid__year=current_month_start.year,
                date_paid__month=current_month_start.month
            )
            total_for_month = month_payments.aggregate(
                total=Coalesce(Sum('amount'), Decimal(0))
            )['total']

            monthly_contributions[current_month_start.strftime(
                '%Y-%m')] = float(total_for_month)

            today = current_month_start - timedelta(days=1)

        context['monthly_contributions_data'] = dict(
            sorted(monthly_contributions.items()))

        return context
