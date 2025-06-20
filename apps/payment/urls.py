# apps/payment/urls.py

from django.urls import path
# Import specific views directly for clarity and to avoid conflicts
from .views import (
    PaymentListView,
    PaymentCreateView,  # <-- CORRECTED: This matches the class name in views.py
    PaymentDetailView,
    PaymentUpdateView,  # <-- Added: For editing payments
    PaymentDeleteView,  # <-- Added: For deleting payments

    # API Endpoints - Make sure these functions exist in views.py!
    search_individuals_api,
    get_individual_family_details_api,
    get_contribution_type_details_api,

    # Uncomment these if you added/plan to add these views
    # PaymentValidateView,
    # PaymentCancelView,
)

# Important for namespacing URLs (e.g., {% url 'payment:add_payment' %})
app_name = 'payment'

urlpatterns = [
    # Main payment list view
    path('', PaymentListView.as_view(), name='payment_list'),

    # Add new payment view (with optional individual_id for pre-selection)
    # Uses PaymentCreateView as per the views.py provided earlier
    path('add/', PaymentCreateView.as_view(), name='add_payment'),
    path('add/<int:individual_id>/', PaymentCreateView.as_view(),  # <-- Uses PaymentCreateView
         name='add_payment_for_individual'),

    # Payment detail view
    path('<int:pk>/', PaymentDetailView.as_view(), name='payment_detail'),

    # Update payment view (added based on our views.py)
    path('<int:pk>/edit/', PaymentUpdateView.as_view(), name='edit_payment'),

    # Delete payment view (added based on our views.py)
    path('<int:pk>/delete/', PaymentDeleteView.as_view(), name='delete_payment'),

    # --- API Endpoints (for JavaScript) ---
    # These refer to function-based views. Ensure these functions are defined in views.py.
    path('api/search_individuals/', search_individuals_api,
         name='api_search_individuals'),
    path('api/individual/<int:pk>/family_details/',
         get_individual_family_details_api, name='api_individual_family_details'),
    path('api/contribution_type/<int:pk>/', get_contribution_type_details_api,
         name='api_contribution_type_details'),

    # --- Optional: Add URLs for Gcash Validation / Cancellation if you use those views ---
    # path('<int:pk>/validate/', PaymentValidateView.as_view(), name='validate_payment'),
    # path('<int:pk>/cancel/', PaymentCancelView.as_view(), name='cancel_payment'),
]
