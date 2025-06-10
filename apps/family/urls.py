# apps/family/urls.py
from django.urls import path
from . import views

app_name = 'family' # Tiyakin na may app_name ang iyong app

urlpatterns = [
    # General Family List
    path('', views.FamilyListView.as_view(), name='family_list'),
    # Family Detail
    path('<int:pk>/', views.FamilyDetailView.as_view(), name='family_detail'),
    # Family Create (General)
    path('create/', views.FamilyCreateView.as_view(), name='family_create'),
    # Family Create (In Church Context)
    path('create/in-church/<int:church_id>/', views.FamilyCreateInChurchView.as_view(), name='family_create_in_church'),
    # Family Update
    path('<int:pk>/edit/', views.FamilyUpdateView.as_view(), name='family_update'),
    # Family Delete
    path('<int:pk>/delete/', views.FamilyDeleteView.as_view(), name='family_delete'),

    # BAGONG URL: Para sa pag-lista ng pamilya sa loob ng isang specific na simbahan
    path('in-church/<int:church_id>/families/', views.FamilyListInChurchView.as_view(), name='church_families'),
]

