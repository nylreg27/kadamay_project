from django.urls import path
# Explicitly import all views for clarity and consistency.
# IMPORTANT: Use the new class-based API views for the URLs.
from .views import (
    PaymentListView,
    PaymentCreateView,
    PaymentDetailView,
    PaymentUpdateView,
    PaymentDeleteView,
    PaymentValidateView,
    PaymentCancelView,
    # These are the new class-based API views:
    IndividualSearchAPIView,
    GetFamilyMembersAPIView,
    GetNextOrNumberAPIView,
    # The old ones might still exist if you didn't delete them,
    # but the URLs should point to the new class-based ones.
    # get_contribution_type_details_api, # This one might still be a function-based view, double-check your views.py
)

app_name = 'payment' # Namespace for URLs, e.g., {% url 'payment:payment_list' %}

urlpatterns = [
    # Core Payment Operations (List, Create, Detail, Update, Delete)
    path('', PaymentListView.as_view(), name='payment_list'),
    path('create/', PaymentCreateView.as_view(), name='payment_create'),
    # Changed Detail path to include '/detail/' for clarity, matching other actions
    path('<int:pk>/detail/', PaymentDetailView.as_view(), name='payment_detail'),
    path('<int:pk>/update/', PaymentUpdateView.as_view(), name='payment_update'),
    path('<int:pk>/delete/', PaymentDeleteView.as_view(), name='payment_delete'),
    
    # Specific Payment Actions (Validate, Cancel)
    path('<int:pk>/validate/', PaymentValidateView.as_view(), name='payment_validate'),
    path('<int:pk>/cancel/', PaymentCancelView.as_view(), name='payment_cancel'),

    # NEW/UPDATED API Endpoints for dynamic data fetching (e.g., for forms via AJAX)
    # Using .as_view() for class-based views
    path('api/search-individuals/', IndividualSearchAPIView.as_view(), name='api_search_individuals'),
    # Changed parameter name to individual_id as used in GetFamilyMembersAPIView
    path('api/get-family-members/<int:individual_id>/', GetFamilyMembersAPIView.as_view(), name='api_get_family_members'),
    path('api/get-next-or-number/', GetNextOrNumberAPIView.as_view(), name='api_get_next_or_number'),
    
    # Keeping this one if it's still a function-based view
    # If you converted this to a class-based view too, update accordingly
    # path('api/contribution-type/<int:pk>/details/', get_contribution_type_details_api, name='api_contribution_type_details'),
]