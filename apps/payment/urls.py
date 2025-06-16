# apps/payment/urls.py

from django.urls import path
from . import views

app_name = 'payment'

urlpatterns = [
    # Existing payment URLs
    path('individual/<int:individual_id>/create/', views.payment_create_full_form_view, name='add_payment'),
    path('list/', views.payment_list_view, name='payment_list'), # Assuming you have this
    path('<int:pk>/detail/', views.payment_detail_view, name='payment_detail'), # Assuming you have this

    # API endpoints (from your payment_form.html JS)
    path('api/individual/<int:individual_id>/family_details/', views.get_family_details_api_view, name='api_family_details'), # Assuming you have this
    
    # === CORRECTED: Renamed the view function to match views.py ===
    path('api/contribution_type/<int:pk>/', views.get_contribution_amount_api_view, name='api_contribution_amount'), 

    # NEW: URL for cancelling a payment
    path('cancel/<int:pk>/', views.cancel_payment_view, name='cancel_payment'),
]

