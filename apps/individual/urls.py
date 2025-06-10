# apps/individual/urls.py
from django.urls import path
from . import views

app_name = 'individual' # Tiyakin na may app_name ang iyong app

urlpatterns = [
    # General Individual List
    path('', views.IndividualListView.as_view(), name='individual_list'),
    # Individual Detail
    path('<int:pk>/', views.IndividualDetailView.as_view(), name='individual_detail'),
    # Individual Create (General)
    path('create/', views.IndividualCreateView.as_view(), name='individual_create'),
    # Individual Update
    path('<int:pk>/edit/', views.IndividualUpdateView.as_view(), name='individual_update'),
    # Individual Delete
    path('<int:pk>/delete/', views.IndividualDeleteView.as_view(), name='individual_delete'),

    # URL para sa pag-lista ng mga indibidwal sa loob ng isang specific na simbahan
    path('in-church/<int:church_id>/individuals/', views.IndividualListInChurchView.as_view(), name='church_individuals'),

    # BAGONG URL: Para sa pag-create ng indibidwal sa loob ng isang specific na pamilya
    path('create/in-family/<int:family_id>/', views.IndividualCreateInFamilyView.as_view(), name='family_individual_create'),
]

