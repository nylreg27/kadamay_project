from django.urls import path
from . import views

app_name = 'issues'

urlpatterns = [
    # Admin issue management
    path('admin/', views.IssueReportListView.as_view(), name='issue_list'),

    # User issue management
    path('', views.UserIssueListView.as_view(), name='user_issue_list'),
    path('create/', views.IssueReportCreateView.as_view(), name='issue_create'),
    path('<int:pk>/', views.IssueReportDetailView.as_view(), name='issue_detail'),
    path('<int:pk>/update/', views.IssueReportUpdateView.as_view(),
         name='issue_update'),
]
