# apps/report/urls.py
from django.urls import path
from .views import DashboardView # Make sure DashboardView is imported correctly

app_name = 'report'

urlpatterns = [
    # Change this line
    path('dashboard/', DashboardView.as_view(), name='dashboard'), # Now it explicitly matches 'dashboard/'
    # If you also want 'report/' to work, you could add:
    # path('', DashboardView.as_view(), name='report_home'), # Example for an alternative
]