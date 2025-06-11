# apps/account/views.py
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
# Use get_user_model() consistently
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group  # For UserRoleForm
from django.views.generic import (
    # Added View for UserRoleAssign/Delete
    ListView, CreateView, UpdateView, DeleteView, View
)
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages  # Import messages for toast notifications
from django import forms  # Import forms for UserRoleForm

from .models import Profile  # Import Profile model
# Import all necessary forms
from .forms import ProfileThemeForm, StyledUserCreationForm, UserLoginForm

User = get_user_model()  # Define User model

# 🔐 Mixins (Keep these as they are useful for permissions)


class ProfileOwnerMixin(UserPassesTestMixin):
    def test_func(self):
        # Ensure the profile exists before trying to get it
        profile_pk = self.kwargs.get('pk')
        if profile_pk:
            profile = get_object_or_404(Profile, pk=profile_pk)
            return profile.user == self.request.user or self.request.user.is_superuser
        return self.request.user.is_authenticated  # Or adjust as per your create logic


class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser

# 🆕 NEW VIEW: User Profile Settings (handles theme and picture)
# Gagamitin natin ito dahil ito ang function-based view sa iyong urls.py


@login_required
def profile_settings(request):
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        # Create a profile if it doesn't exist (should be rare if signals are working)
        profile = Profile.objects.create(user=request.user)
        messages.info(request, "A profile has been created for your account.")

    if request.method == 'POST':
        form = ProfileThemeForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(
                request, "Your profile settings have been updated successfully!")
            return redirect('account:profile_settings')
        else:
            messages.error(
                request, "There was an error updating your profile settings. Please check the form.")
    else:
        form = ProfileThemeForm(instance=profile)

    context = {
        'form': form,
        'current_theme': profile.theme if profile.theme else 'corporate',
        'current_profile_picture': profile.profile_picture.url if profile.profile_picture else None,
    }
    return render(request, 'account/profile_settings.html', context)


# 👮‍♂️ User Management (Admin Only) - Keep these for admin functionality
class UserListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = User
    template_name = 'account/user_list.html'
    context_object_name = 'users'
    paginate_by = 20

    def get_queryset(self):
        return User.objects.order_by('username')


class UserCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = User
    form_class = StyledUserCreationForm  # Use the correct form
    template_name = 'account/user_form.html'
    success_url = reverse_lazy('account:user_list')

    def form_valid(self, form):
        messages.success(self.request, "User created successfully!")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(
            self.request, "Error creating user. Please check the form.")
        return super().form_invalid(form)


class UserUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = User
    fields = ['username', 'email', 'first_name', 'last_name', 'is_active',
              'is_staff', 'is_superuser']  # Added more relevant fields
    template_name = 'account/user_form.html'
    success_url = reverse_lazy('account:user_list')

    def form_valid(self, form):
        messages.success(self.request, "User updated successfully!")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(
            self.request, "Error updating user. Please check the form.")
        return super().form_invalid(form)


class UserDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = User
    template_name = 'account/user_confirm_delete.html'
    success_url = reverse_lazy('account:user_list')

    def form_valid(self, form):
        messages.success(self.request, "User deleted successfully!")
        return super().form_valid(form)


# 🔁 Role Management (Keep these)
class UserRoleForm(forms.Form):
    role = forms.ModelChoiceField(
        queryset=Group.objects.all(), label='Assign Role')


class UserRoleAssignView(LoginRequiredMixin, AdminRequiredMixin, View):
    template_name = 'account/user_role_form.html'

    def get(self, request, user_id):
        user = get_object_or_404(User, pk=user_id)
        form = UserRoleForm()
        return render(request, self.template_name, {'form': form, 'user': user})

    def post(self, request, user_id):
        user = get_object_or_404(User, pk=user_id)
        form = UserRoleForm(request.POST)
        if form.is_valid():
            user.groups.add(form.cleaned_data['role'])
            user.save()
            messages.success(
                request, f"Role assigned to {user.username} successfully!")
            return redirect('account:user_list')
        messages.error(
            request, "Failed to assign role. Please check the form.")
        return render(request, self.template_name, {'form': form, 'user': user})


class UserRoleDeleteView(LoginRequiredMixin, AdminRequiredMixin, View):
    def post(self, request, user_id):
        user = get_object_or_404(User, pk=user_id)
        user.groups.clear()
        user.save()
        messages.success(
            request, f"Roles cleared for {user.username} successfully!")
        return redirect('account:user_list')


class RegisterView(CreateView):
    template_name = 'registration/register.html'
    form_class = StyledUserCreationForm  # Use the correct form
    success_url = reverse_lazy('account:login')  # Changed to account:login

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request, "Account created successfully. Please log in.")
        return response

    def form_invalid(self, form):
        messages.error(
            self.request, "There was an error in your registration. Please check the form.")
        return super().form_invalid(form)


# --- PROFILE SETTINGS VIEW ---
class ProfileSettingsView(LoginRequiredMixin, UpdateView):
    model = Profile
    form_class = ProfileThemeForm
    template_name = 'account/profile_settings.html'
    # Redirect back to settings page on success
    success_url = reverse_lazy('account:profile_settings')

    def get_object(self):
        # This ensures the view works with the *current logged-in user's* profile
        # instead of requiring a pk in the URL.
        return self.request.user.profile

    def form_valid(self, form):
        messages.success(
            self.request, 'Your profile settings have been updated successfully!')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(
            self.request, 'There was an error updating your profile. Please check the form.')
        return super().form_invalid(form)
