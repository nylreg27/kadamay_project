from django.urls import path
from . import views

app_name = 'payment'

urlpatterns = [
    # Contribution type URLs
    path('contribution-types/', views.ContributionTypeListView.as_view(), name='contribution_type_list'),
    path('contribution-types/create/', views.ContributionTypeCreateView.as_view(), name='contribution_type_create'),
    path('contribution-types/<int:pk>/', views.ContributionTypeDetailView.as_view(), name='contribution_type_detail'),
    path('contribution-types/<int:pk>/update/', views.ContributionTypeUpdateView.as_view(), name='contribution_type_update'),
    path('contribution-types/<int:pk>/delete/', views.ContributionTypeDeleteView.as_view(), name='contribution_type_delete'),
    
    # Payment URLs
    path('payments/', views.PaymentListView.as_view(), name='payment_list'),
    path('payments/create/', views.PaymentCreateView.as_view(), name='payment_create'),
    path('payments/<int:pk>/', views.PaymentDetailView.as_view(), name='payment_detail'),
    path('payments/<int:pk>/update/', views.PaymentUpdateView.as_view(), name='payment_update'),
    path('payments/<int:pk>/delete/', views.PaymentDeleteView.as_view(), name='payment_delete'),
    
    # Individual-specific payment URLs
    path('individual/<int:individual_id>/payments/', views.PaymentListView.as_view(), name='individual_payments'),
    path('individual/<int:individual_id>/payments/create/', views.PaymentCreateView.as_view(), name='individual_payment_create'),
]