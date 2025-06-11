# apps/account/urls.py
from django.urls import path
# Import Django's default auth views
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy  # Import reverse_lazy for success_url
from . import views  # Single import for views
from .forms import UserLoginForm  # Assuming you have a custom login form

app_name = 'account'  # Tiyakin na may app_name ang iyong app

urlpatterns = [
    # User management (admin only)
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/create/', views.UserCreateView.as_view(), name='user_create'),
    path('users/<int:pk>/edit/', views.UserUpdateView.as_view(), name='user_edit'),
    path('users/<int:pk>/delete/',
         views.UserDeleteView.as_view(), name='user_delete'),

    # User church role management
    path('users/<int:user_id>/role/',
         views.UserRoleAssignView.as_view(), name='user_role'),
    path('users/<int:user_id>/role/delete/',
         views.UserRoleDeleteView.as_view(), name='user_role_delete'),

    # User Profile Settings (Ito na ang FINAL na URL para sa profile settings)
    path('profile-settings/', views.profile_settings, name='profile_settings'),

    # Custom registration
    path('register/', views.RegisterView.as_view(), name='register'),

    # Custom login (using Django's default LoginView with your custom form)
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html',
                                                authentication_form=UserLoginForm), name='login'),

    # Logout (using Django's default LogoutView)
    path('logout/', auth_views.LogoutView.as_view(next_page=reverse_lazy('account:login')), name='logout'),

    # Password Change (using Django's default views)
    path('password_change/', auth_views.PasswordChangeView.as_view(template_name='registration/password_change_form.html',
                                                                   success_url=reverse_lazy('account:password_change_done')), name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='registration/password_change_done.html'), name='password_change_done'),

    path('profile/settings/', views.ProfileSettingsView.as_view(),
         name='profile_settings'),
]
