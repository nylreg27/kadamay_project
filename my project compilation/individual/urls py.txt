# apps/individual/urls.py
from django.urls import path
from . import views

app_name = 'individual'

urlpatterns = [
    # Dashboard URL
    path('dashboard/', views.IndividualDashboardView.as_view(),
         name='individual_dashboard'),

    # API URL for fetching individual details (MODIFIED to include payments)
    path('<int:pk>/details/', views.individual_details_api,
         name='individual_details_api'),

    # General Individual List
    path('', views.IndividualListView.as_view(), name='individual_list'),

    # Individual Detail 
    path('<int:pk>/', views.IndividualDetailView.as_view(),
         name='individual_detail'),

    # Individual Create (General)
    path('create/', views.IndividualCreateView.as_view(), name='individual_create'),

    # Individual Update
    path('<int:pk>/edit/', views.IndividualUpdateView.as_view(),
         name='individual_update'),

    # Individual Delete
    path('<int:pk>/delete/', views.IndividualDeleteView.as_view(),
         name='individual_delete'),

    # URL for listing individuals within a specific church
    path('in-church/<int:church_id>/individuals/',
         views.IndividualListInChurchView.as_view(), name='church_individuals'),

    # NEW URL: For creating an individual within a specific family context
    path('create/in-family/<int:family_id>/',
         views.IndividualCreateInFamilyView.as_view(), name='family_individual_create'),
    
    # NOTE: The PaymentCreateView URL from your snippet was pointing here.
    # It should be in payment/urls.py. The payment:add_payment URL is already handled there.
    # So, no change needed here regarding payment creation URL.
]

