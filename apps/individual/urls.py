# apps/individual/urls.py

from django.urls import path
# Import all views needed, including the new IndividualCreateForFamilyView
from .views import (
    IndividualCreateView,
    IndividualDetailView,
    IndividualUpdateView,
    IndividualListView,
    IndividualDeleteView,
    IndividualListByChurchView,  # From previous fix
    # NEW: Import the view for creating individual for a family
    IndividualCreateForFamilyView
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

    # List individuals by Church ID (from previous fix)
    path('church/<int:church_id>/', IndividualListByChurchView.as_view(),
         name='church_individuals'),

    # NEW: Create an individual tied to a specific family
    # This matches {% url 'individual:family_individual_create' family.pk %}
    path('family/<int:family_id>/create/',
         IndividualCreateForFamilyView.as_view(), name='family_individual_create'),
]
