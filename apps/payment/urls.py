from django.urls import path
# Explicitly import all views for clarity and consistency
from .views import PaymentListView, PaymentCreateView, PaymentDetailView, \
    PaymentUpdateView, PaymentDeleteView, PaymentValidateView, PaymentCancelView, \
    search_individuals_api, get_individual_family_details_api, get_contribution_type_details_api

# Namespace for URLs, e.g., {% url 'payment:payment_list' %}
app_name = 'payment'

urlpatterns = [
    # Core Payment Operations (List, Create, Detail, Update, Delete)
    path('', PaymentListView.as_view(), name='payment_list'),
    # Changed from 'add/' and 'add_payment'
    path('create/', PaymentCreateView.as_view(), name='payment_create'),
    path('<int:pk>/', PaymentDetailView.as_view(), name='payment_detail'),
    # Changed from 'edit/' and 'payment_edit'
    path('<int:pk>/update/', PaymentUpdateView.as_view(), name='payment_update'),
    path('<int:pk>/delete/', PaymentDeleteView.as_view(), name='payment_delete'),

    # Specific Payment Actions (Validate, Cancel)
    path('<int:pk>/validate/', PaymentValidateView.as_view(),
         name='payment_validate'),
    path('<int:pk>/cancel/', PaymentCancelView.as_view(), name='payment_cancel'),

    # API Endpoints for dynamic data fetching (e.g., for forms via AJAX)
    path('api/search-individuals/', search_individuals_api,
         name='api_search_individuals'),  # Path and name maintained
    path('api/individual/<int:pk>/family-details/',
         # Path and name maintained
         get_individual_family_details_api, name='api_individual_family_details'),
    path('api/contribution-type/<int:pk>/details/',
         # Path and name maintained
         get_contribution_type_details_api, name='api_contribution_type_details'),
]
