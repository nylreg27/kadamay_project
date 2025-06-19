# apps/individual/urls.py

from django.urls import path
# Import all views needed, including the new IndividualSearchAPIView
from .views import (
    IndividualCreateView,
    IndividualDetailView,
    IndividualUpdateView,
    IndividualListView,
    IndividualDeleteView,
    IndividualListByChurchView,
    IndividualCreateForFamilyView,
    IndividualSearchAPIView  # NEW: Import the new API view
)

# Crucial for reverse lookups like {% url 'individual:individual_list' %}
app_name = 'individual'

urlpatterns = [
    # List view for all individuals
    path('', IndividualListView.as_view(), name='individual_list'),

    # Create new individual (general create)
    path('create/', IndividualCreateView.as_view(), name='individual_create'),

    # Detail view for a specific individual
    path('<int:pk>/', IndividualDetailView.as_view(), name='individual_detail'),

    # Update an existing individual
    path('<int:pk>/update/', IndividualUpdateView.as_view(),
         name='individual_update'),

    # Delete an individual
    path('<int:pk>/delete/', IndividualDeleteView.as_view(),
         name='individual_delete'),

    # List individuals by Church ID
    path('church/<int:church_id>/', IndividualListByChurchView.as_view(),
         name='church_individuals'),

    # Create an individual tied to a specific family
    path('family/<int:family_id>/create/',
         IndividualCreateForFamilyView.as_view(), name='family_individual_create'),

    # NEW: API endpoint for searching individuals
    # This will be called by JavaScript for the "Head of Family" search
    path('api/search/', IndividualSearchAPIView.as_view(),
         name='individual_search_api'),
]
