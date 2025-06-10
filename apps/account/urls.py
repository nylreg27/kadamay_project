# apps/account/urls.py
from django.urls import path
from . import views # Single import for views, mas malinis

app_name = 'account' # Tiyakin na may app_name ang iyong app

urlpatterns = [
    # User management (admin only) - Adjusted for clarity and removed duplicates
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/create/', views.UserCreateView.as_view(), name='user_create'),
    path('users/<int:pk>/edit/', views.UserUpdateView.as_view(), name='user_edit'), # Naka-isa na lang
    path('users/<int:pk>/delete/', views.UserDeleteView.as_view(), name='user_delete'),

    # User church role management (Assuming these are still correct)
    path('users/<int:user_id>/role/', views.UserRoleAssignView.as_view(), name='user_role'),
    path('users/<int:user_id>/role/delete/', views.UserRoleDeleteView.as_view(), name='user_role_delete'),

    # User Profile Settings (NEW and CORRECT URL)
    # Ito ang hinahanap ng base.html
    path('profile-settings/', views.profile_settings, name='profile_settings'),
    
    path('', views.UserListView.as_view(), name='user_list'),
]