# apps/payment/urls.py

from django.urls import path
from . import views

app_name = 'payment'

urlpatterns = [
    # API endpoint to get contribution type details (e.g., default amount)
    path('api/contribution_type/<int:pk>/',
         views.contribution_type_detail_api, name='contribution_type_detail_api'),

    # NEW API endpoint: To fetch family members and related info for an individual dynamically
    path('api/individual/<int:individual_id>/family_details/',
         views.get_individual_family_details_api, name='get_individual_family_details_api'),

    # List all payments
    path('list/', views.PaymentListView.as_view(), name='payment_list'),

    # --- MAIN PAYMENT CREATION FORM DISPLAY (Handles GET request from dashboard) ---
    # This URL will display the payment form for a specific individual.
    path('individual/<int:individual_id>/create/',  # Renamed from /payments/create/ to just /create/ for clarity
         # <--- This view handles the GET request to display the form
         views.payment_create_full_form_view,
         name='payment_create_for_individual'),

    # --- PAYMENT FORM SUBMISSION (Handles POST request from the form) ---
    # This URL receives the submitted form data.
    path('add/',
         # <--- This view handles the POST request (form submission)
         views.payment_create_view,
         name='add_payment'),

    # --- Existing Payment Detail, Update, Delete Views ---
    path('<int:pk>/detail/', views.payment_detail_view, name='payment_detail'),
    path('<int:pk>/update/', views.payment_update_view, name='payment_update'),
    path('<int:pk>/delete/', views.payment_delete_view, name='payment_delete'),
]
