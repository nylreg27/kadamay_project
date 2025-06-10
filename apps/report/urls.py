from django.urls import path
from .views import DashboardView

app_name = 'report'

urlpatterns = [
    path('', DashboardView.as_view(), name='dashboard'),
]
