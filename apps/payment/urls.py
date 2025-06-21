# apps/payment/urls.py

from django.urls import path
# Change this line:
# from . import views
# To this:
from .views import PaymentListView, PaymentCreateView, PaymentDetailView, \
    PaymentUpdateView, PaymentDeleteView, PaymentValidateView, PaymentCancelView, \
    search_individuals_api, get_individual_family_details_api, get_contribution_type_details_api

app_name = 'payment'

urlpatterns = [
    path('', PaymentListView.as_view(), name='payment_list'),
    path('add/', PaymentCreateView.as_view(), name='add_payment'),
    path('<int:pk>/', PaymentDetailView.as_view(), name='payment_detail'),
    path('<int:pk>/edit/', PaymentUpdateView.as_view(), name='payment_edit'),
    path('<int:pk>/delete/', PaymentDeleteView.as_view(), name='payment_delete'),
    path('<int:pk>/validate/', PaymentValidateView.as_view(),
         name='payment_validate'),
    path('<int:pk>/cancel/', PaymentCancelView.as_view(), name='payment_cancel'),

    # API Endpoints
    path('api/search-individuals/', search_individuals_api,
         name='api_search_individuals'),
    path('api/individual/<int:pk>/family-details/',
         get_individual_family_details_api, name='api_individual_family_details'),
    path('api/contribution-type/<int:pk>/details/',
         get_contribution_type_details_api, name='api_contribution_type_details'),
]
