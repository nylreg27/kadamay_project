# apps/payment/urls.py

from django.urls import path
from . import views

app_name = 'payment'

urlpatterns = [
    # Payment Creation for a specific individual
    # Now: payment/create/individual/<id>/
    path('create/individual/<int:individual_id>/', views.payment_create_full_form_view, name='add_payment'),
    
    # General Payment List (All payments)
    # Now: payment/all/
    path('all/', views.payment_list_view, name='payment_list'), 
    
    # Specific Payment Details - === IMPORTANT FIX HERE ===
    # From: path('<int:pk>/detail/', views.payment_detail_view, name='payment_detail'), (this was in your error traceback)
    # To:   path('<int:pk>/', ...) for a cleaner root-level detail path to match JS
    path('<int:pk>/', views.payment_detail_view, name='payment_detail'), 
    
    # Cancellation of a specific payment (nested under payment PK)
    # Now: payment/<id>/cancel/
    path('<int:pk>/cancel/', views.cancel_payment_view, name='cancel_payment'),

    # API endpoints (usually kept separate)
    path('api/individual/<int:individual_id>/family_details/', views.get_family_details_api_view, name='api_family_details'), 
    path('api/contribution_type/<int:pk>/', views.get_contribution_amount_api_view, name='api_contribution_amount'), 

    # URLs for Payment Validation Workflow (grouped under 'admin/')
    # Now: payment/admin/pending/
    path('admin/pending/', views.pending_payments_list_view, name='pending_payments_list'),
    
    # Validate a specific payment by Admin
    # Now: payment/admin/validate/<id>/
    path('admin/validate/<int:pk>/', views.validate_payment_view, name='validate_payment'),
]

