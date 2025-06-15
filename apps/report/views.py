# apps/report/views.py
from django.views.generic import View
from django.shortcuts import render
from django.db.models import Count, Sum, F, ExpressionWrapper, fields
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.church.models import Church
from apps.family.models import Family
from apps.individual.models import Individual
from apps.payment.models import Payment # Assuming you have a Payment model

class DashboardView(LoginRequiredMixin, View):
    template_name = 'report/dashboard.html'

    def get(self, request, *args, **kwargs):
        if request.user.is_superuser:
            churches = Church.objects.all()
        else:
            # Ito ay assuming na ang UserChurch model mo ay nag-a-assign ng simbahan sa user
            # Kung iba ang logic mo sa pag-assign ng simbahan sa user, kailangan itong baguhin.
            user_church_assignment = request.user.assigned_church.first()
            if user_church_assignment:
                churches = Church.objects.filter(id=user_church_assignment.church.id)
            else:
                churches = Church.objects.none()

        church_ids = [church.id for church in churches]

        individual_queryset = Individual.objects.filter(family__church__id__in=church_ids)


        # Total Counts
        total_churches = churches.count()
        total_families = Family.objects.filter(church__id__in=church_ids).count()
        total_members = individual_queryset.count()

        # Active, Deceased, and Inactive-but-Alive Members
        active_members_count = individual_queryset.filter(is_active_member=True, is_alive=True).count()
        
        # FIXED: Binago ang variable names para tugma sa template
        inactive_deceased = individual_queryset.filter(is_alive=False).count() # Ito ang mga miyembro na patay na
        inactive_alive = individual_queryset.filter(is_active_member=False, is_alive=True).count() # Mga miyembro na hindi active pero buhay pa


        # Payments related to these churches
        total_payments = Payment.objects.filter(individual__family__church__id__in=church_ids).aggregate(total_amount=Sum('amount'))['total_amount'] or 0

        # Recent members (adjust as needed, e.g., last 5)
        recent_members = individual_queryset.order_by('-date_added')[:5]

        context = {
            'total_churches': total_churches,
            'total_families': total_families,
            'total_members': total_members,
            'active_members': active_members_count, # FIXED: Binago ang pangalan
            'inactive_deceased': inactive_deceased, # FIXED: Binago ang pangalan
            'inactive_alive': inactive_alive,       # FIXED: Binago ang pangalan
            'total_payments': total_payments,
            'recent_members': recent_members,
            'title': 'System Dashboard',
        }
        return render(request, self.template_name, context)

