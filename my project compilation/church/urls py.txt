# apps/church/urls.py (Full and Corrected Version)

from django.urls import path
from . import views

app_name = 'church'

urlpatterns = [
    path('', views.ChurchListView.as_view(), name='church_list'),
    path('create/', views.ChurchCreateView.as_view(), name='church_create'),
    path('<int:pk>/', views.ChurchDetailView.as_view(), name='church_detail'),
    path('<int:pk>/update/', views.ChurchUpdateView.as_view(), name='church_update'),
    path('<int:pk>/delete/', views.ChurchDeleteView.as_view(), name='church_delete'),
    path('dashboard/', views.dashboard, name='dashboard'),
    # URLs for Family list and creation within a specific church
    path('<int:church_id>/families/', views.FamilyListInChurchView.as_view(),
         name='families_in_church_list'),
    path('<int:church_id>/families/create/',
         views.FamilyCreateInChurchView.as_view(), name='family_create_in_church'),
]
