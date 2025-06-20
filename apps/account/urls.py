# apps/account/urls.py

# Make sure 'include' is imported for auth.urls
from django.urls import path, include
from django.contrib.auth import views as auth_views  # Django's default auth views
from django.urls import reverse_lazy  # For success_url redirects

# Import specific views from your apps.account.views module
from .views import (
    UserListView,
    UserCreateView,
    UserUpdateView,
    UserDeleteView,
    UserRoleAssignView,
    UserRoleDeleteView,
    RegisterView,
    ProfileSettingsView,  # This is your class-based ProfileSettingsView
)

from .forms import UserLoginForm  # Assuming you have a custom login form

# Essential for namespacing (e.g., {% url 'account:login' %})
app_name = 'account'

urlpatterns = [
    # IMPORTANT: Include Django's built-in authentication URLs here FIRST.

    path('', include('django.contrib.auth.urls')),

    # --- Your Custom Login URL (If you need to override the default for your custom form/template) ---
    # This needs to come AFTER the include if you want it to take precedence
    # for the 'login' URL name.
    path('login/', auth_views.LoginView.as_view(
        template_name='registration/login.html',
        authentication_form=UserLoginForm,
        redirect_authenticated_user=True,
    ), name='login'),  # This will override 'account:login' from auth.urls with your custom form

    # --- Your Custom Register View ---
    path('register/', RegisterView.as_view(), name='register'),

    # --- User Profile Settings (Using the Class-Based View) ---
    # We changed the name to 'user_profile_settings' to be unique and clear.
    path('profile/settings/', ProfileSettingsView.as_view(),
         name='user_profile_settings'),


    # --- User Management (Admin/Superuser specific) ---
    path('users/', UserListView.as_view(), name='user_list'),
    path('users/create/', UserCreateView.as_view(), name='user_create'),
    path('users/<int:pk>/edit/', UserUpdateView.as_view(), name='user_edit'),
    path('users/<int:pk>/delete/', UserDeleteView.as_view(), name='user_delete'),

    # --- User Church Role Management ---
    path('users/<int:user_id>/role/',
         UserRoleAssignView.as_view(), name='user_role_assign'),
    path('users/<int:user_id>/role/delete/',
         UserRoleDeleteView.as_view(), name='user_role_delete'),
]

# Note: The standard 'logout', 'password_change', 'password_reset', etc.
# URLs are now provided by `path('', include('django.contrib.auth.urls'))`.
# Any links in your templates should use their namespaced versions, e.g.,
# `{% url 'account:password_change' %}`.
