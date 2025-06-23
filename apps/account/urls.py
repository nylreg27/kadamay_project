# apps/account/urls.py

from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views  # Import all views from this app

app_name = 'account'  # Define app_name for namespacing URLs

urlpatterns = [
    # User creation form (using Class-Based View)
    path('users/create/', views.UserCreateView.as_view(), name='user_create'),
    # User list (using Class-Based View)
    path('users/', views.UserListView.as_view(), name='user_list'),
    # User update (using Class-Based View)
    path('users/<int:pk>/update/',
         views.UserUpdateView.as_view(), name='user_update'),
    # User delete (using Class-Based View)
    path('users/<int:pk>/delete/',
         views.UserDeleteView.as_view(), name='user_delete'),

    # Role Management
    path('users/<int:user_id>/assign_role/',
         views.UserRoleAssignView.as_view(), name='assign_role'),
    path('users/<int:user_id>/clear_roles/',
         views.UserRoleDeleteView.as_view(), name='clear_roles'),

    # KINI ANG KINAHANGLAN NIMO IDUGANG PARA SA 'CREATE IN-CHARGE':
    # Assuming kini Class-Based View. Palihug i-adjust ang 'UserCreateInchargeView'
    # kung lahi ang ngalan sa imong actual nga view sa views.py
    path('create_incharge/', views.UserCreateInchargeView.as_view(),
         name='create_incharge'),


    # Authentication URLs
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html',
                                                authentication_form=views.UserLoginForm), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Registration
    path('register/', views.RegisterView.as_view(), name='register'),

    # Profile Settings (using Class-Based View)
    path('profile/', views.ProfileSettingsView.as_view(), name='profile'),

    # Password Change (using Django's built-in views - templates needed for these)
    path('password_change/', auth_views.PasswordChangeView.as_view(template_name='account/password_change.html',
                                                                   success_url=reverse_lazy('account:password_change_done')), name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='account/password_change_done.html'), name='password_change_done'),

    # Password Reset (requires email configuration)
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='account/password_reset_form.html',
                                                                 email_template_name='account/password_reset_email.html', success_url=reverse_lazy('account:password_reset_done')), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='account/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='account/password_reset_confirm.html',
                                                                                success_url=reverse_lazy('account:password_reset_complete')), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='account/password_reset_complete.html'), name='password_reset_complete'),
]
