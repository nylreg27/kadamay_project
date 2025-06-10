# apps/account/views.py
from django import forms
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.contrib.auth.models import User, Group
from django.views import View
from django.views.generic import (
    ListView, CreateView, UpdateView, DetailView, DeleteView
)
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin # BAGONG IMPORT: Idinagdag ang LoginRequiredMixin
from django.contrib.auth.decorators import login_required # BAGONG IMPORT: para sa @login_required decorator
from django.contrib import messages # Import messages for toast notifications

from .models import Profile # Import Profile model
from .forms import ProfileThemeForm, StyledUserCreationForm # Import our forms, including StyledUserCreationForm

# 🔐 Mixins (Keep these as they are useful for permissions)
class ProfileOwnerMixin(UserPassesTestMixin):
    def test_func(self):
        # Ensure the profile exists before trying to get it
        profile_pk = self.kwargs.get('pk')
        if profile_pk:
            profile = get_object_or_404(Profile, pk=profile_pk)
            return profile.user == self.request.user or self.request.user.is_superuser
        # If no PK, maybe it's a create view for a new profile
        return self.request.user.is_authenticated # Or adjust as per your create logic

class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser

# 🆕 NEW VIEW: User Profile Settings (handles theme and picture)
@login_required
def profile_settings(request):
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        # Create a profile if it doesn't exist (this should be caught by fix_profiles, but as a fallback)
        profile = Profile.objects.create(user=request.user)
        messages.info(request, "A profile has been created for your account.")

    if request.method == 'POST':
        form = ProfileThemeForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile settings have been updated successfully!")
            return redirect('account:profile_settings')
        else:
            messages.error(request, "There was an error updating your profile settings. Please check the form.")
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


# Removed: Re-defined UserCreateForm within views.py for clarity if not in forms.py
# The form is now imported from forms.py

class UserCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = User
    form_class = StyledUserCreationForm # Now using StyledUserCreationForm from forms.py
    template_name = 'account/user_form.html'
    success_url = reverse_lazy('account:user_list')


class UserUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = User
    fields = ['username', 'email', 'first_name', 'last_name']
    template_name = 'account/user_form.html'
    success_url = reverse_lazy('account:user_list')


class UserDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = User
    template_name = 'account/user_confirm_delete.html'
    success_url = reverse_lazy('account:user_list')


# 🔁 Role Management (Keep these)
class UserRoleForm(forms.Form):
    role = forms.ModelChoiceField(queryset=Group.objects.all(), label='Assign Role')


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
            messages.success(request, f"Role assigned to {user.username} successfully!")
            return redirect('account:user_list')
        messages.error(request, "Failed to assign role. Please check the form.")
        return render(request, self.template_name, {'form': form, 'user': user})


class UserRoleDeleteView(LoginRequiredMixin, AdminRequiredMixin, View):
    def post(self, request, user_id):
        user = get_object_or_404(User, pk=user_id)
        user.groups.clear()
        user.save()
        messages.success(request, f"Roles cleared for {user.username} successfully!")
        return redirect('account:user_list')
