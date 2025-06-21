# apps/account/urls.py

# Make sure 'include' is imported for auth.urls
from django.urls import path, include
# No need for `from . import views` if you're importing classes directly.
# But keeping it if you might use views.some_function later. For now, let's stick to explicit imports.

from django.contrib.auth import views as auth_views  # Django's default auth views
# from django.urls import reverse_lazy  # reverse_lazy is used in views.py, not always directly in urls.py for path definition

from .views import (
    UserListView,
    UserCreateView,
    UserUpdateView,
    UserDeleteView,
    UserRoleAssignView,
    UserRoleDeleteView,
    RegisterView,
    ProfileSettingsView, # Import ProfileSettingsView direkta
)

from .forms import UserLoginForm  # Assuming you have a custom login form

# Essential for namespacing (e.g., {% url 'account:login' %})
app_name = 'account'

urlpatterns = [
    # IMPORTANT: Include Django's built-in authentication URLs here FIRST.
    # This provides 'logout', 'password_change', 'password_change_done', 'password_reset', etc.
    # The names will be 'account:logout', 'account:password_change', etc.
    path('', include('django.contrib.auth.urls')),

    # --- Your Custom Login URL (If you need to override the default for your custom form/template) ---
    # Only keep this if your 'registration/login.html' is specific and not picked up by default.
    # Make sure 'name='login' matches the default behavior of `django.contrib.auth.urls`
    # or give it a unique name if you want both login pages.
    # For simplicity, if `path('', include('django.contrib.auth.urls'))` already provides a good login view,
    # you might not need this custom one.
    path('login/', auth_views.LoginView.as_view(
        template_name='registration/login.html',
        authentication_form=UserLoginForm,
        redirect_authenticated_user=True,
    ), name='login'),

    # --- Your Custom Register View ---
    path('register/', RegisterView.as_view(), name='register'),

    # --- MAIN PROFILE PAGE (View/Edit) ---
    path('profile/', ProfileSettingsView.as_view(), name='profile'),

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