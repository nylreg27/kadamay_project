# apps/payment/urls.py

from django.urls import path
from . import views
from .views import (
    PaymentListView,
    AddPaymentView,
    PaymentDetailView,
    search_individuals_api,
    get_individual_family_details_api,
    get_contribution_type_details_api,
)

# Important for namespacing URLs (e.g., {% url 'payment:add_payment' %})
app_name = 'payment'

urlpatterns = [
    # Main payment list view
    path('', PaymentListView.as_view(), name='payment_list'),

    # Add new payment view (with optional individual_id for pre-selection)
    path('add/', AddPaymentView.as_view(), name='add_payment'),
    path('add/<int:individual_id>/', AddPaymentView.as_view(),
         name='add_payment_for_individual'),

    # Payment detail view
    path('<int:pk>/', PaymentDetailView.as_view(), name='payment_detail'),

    # --- API Endpoints (for JavaScript) ---
    path('api/search_individuals/', search_individuals_api,
         name='api_search_individuals'),
    path('api/individual/<int:pk>/family_details/',
         get_individual_family_details_api, name='api_individual_family_details'),
    path('api/contribution_type/<int:pk>/', get_contribution_type_details_api,
         name='api_contribution_type_details'),

    path('create/', views.create_payment,
         name='create_payment'),  # Added this line!
]
