# apps/individual/urls.py
from django.urls import path
from . import views

app_name = 'individual'

urlpatterns = [
    # Dashboard URL (COMMENTED OUT - NOT NEEDED FOR PAYMENT FORM)
    path('dashboard/', views.IndividualDashboardView.as_view(),
         name='individual_dashboard'),

    # API URL for fetching details (might be used for individual dropdowns outside payment app)
    path('<int:pk>/details/', views.individual_details_api,
         name='individual_details_api'),

    # General Individual List (COMMENTED OUT - NOT NEEDED FOR PAYMENT FORM)
    path('', views.IndividualListView.as_view(), name='individual_list'),

    # Individual Detail (COMMENTED OUT - NOT NEEDED FOR PAYMENT FORM)
    path('<int:pk>/', views.IndividualDetailView.as_view(),
         name='individual_detail'),

    # Individual Create (General) (COMMENTED OUT - NOT NEEDED FOR PAYMENT FORM)
    path('create/', views.IndividualCreateView.as_view(), name='individual_create'),

    # Individual Update (COMMENTED OUT - NOT NEEDED FOR PAYMENT FORM)
    path('<int:pk>/edit/', views.IndividualUpdateView.as_view(),
         name='individual_update'),

    # Individual Delete (COMMENTED OUT - NOT NEEDED FOR PAYMENT FORM)
    path('<int:pk>/delete/', views.IndividualDeleteView.as_view(),
         name='individual_delete'),

    # URL for listing individuals within a specific church (COMMENTED OUT - NOT NEEDED FOR PAYMENT FORM)
    path('in-church/<int:church_id>/individuals/',
         views.IndividualListInChurchView.as_view(), name='church_individuals'),

    # NEW URL: For creating an individual within a specific family context (COMMENTED OUT - NOT NEEDED FOR PAYMENT FORM)
    path('create/in-family/<int:family_id>/',
         views.IndividualCreateInFamilyView.as_view(), name='family_individual_create'),
]
