# apps/account/views.py
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.views.generic import (
    ListView, CreateView, UpdateView, DeleteView, View
)
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.contrib import messages
from django import forms

from .models import Profile
from .forms import ProfileThemeForm, UserDetailsForm, StyledUserCreationForm, UserLoginForm

User = get_user_model()

# 🔐 Mixins (Keep these)
class ProfileOwnerMixin(UserPassesTestMixin):
    def test_func(self):
        profile_pk = self.kwargs.get('pk')
        if profile_pk:
            profile = get_object_or_404(Profile, pk=profile_pk)
            return profile.user == self.request.user or self.request.user.is_superuser
        return self.request.user.is_authenticated

class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser

# --- REMOVED: user_profile_view (function-based) ---
# Dili na ni nato gamiton kay ang ProfileSettingsView na ang bahala sa tanan.
# @login_required
# def user_profile_view(request):
#     # ... (code para sa read-only view) ...
#     return render(request, 'account/profile_detail.html', context)


# 👮‍♂️ User Management (Admin Only) - Keep these
class UserListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = User
    template_name = 'account/user_list.html'
    context_object_name = 'users'
    paginate_by = 20

    def get_queryset(self):
        return User.objects.order_by('username')

class UserCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = User
    form_class = StyledUserCreationForm
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
              'is_staff', 'is_superuser']
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
    form_class = StyledUserCreationForm
    success_url = reverse_lazy('account:login')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request, "Account created successfully. Please log in.")
        return response

    def form_invalid(self, form):
        messages.error(
            self.request, "There was an error in your registration. Please check the form.")
        return super().form_invalid(form)


# --- PROFILE SETTINGS VIEW (Ang atong gigamit karon) ---
class ProfileSettingsView(LoginRequiredMixin, View): # Importante gihapon View ni, dili UpdateView
    template_name = 'account/profile_settings.html'

    def get_context_data(self, **kwargs):
        context = {}
        try:
            profile = self.request.user.profile
        except Profile.DoesNotExist:
            profile = Profile.objects.create(user=self.request.user)

        context['profile_form'] = ProfileThemeForm(instance=profile)
        context['user_form'] = UserDetailsForm(instance=self.request.user) # UserDetailsForm for First Name, Last Name, Email

        context['user_status'] = "Active" if self.request.user.is_active else "Inactive"
        user_type_list = []
        if self.request.user.is_superuser:
            user_type_list.append("Admin")
        if self.request.user.is_staff:
            user_type_list.append("Staff")
        for group in self.request.user.groups.all():
            user_type_list.append(group.name)
        context['user_type'] = ", ".join(sorted(list(set(user_type_list)))) if user_type_list else "Regular User"

        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        try:
            profile = request.user.profile
        except Profile.DoesNotExist:
            profile = Profile.objects.create(user=request.user)

        profile_form = ProfileThemeForm(request.POST, request.FILES, instance=profile)
        user_form = UserDetailsForm(request.POST, instance=request.user)

        if profile_form.is_valid() and user_form.is_valid():
            profile_form.save()
            user_form.save()
            messages.success(request, 'Your profile settings have been updated successfully!')
            return redirect('account:profile') # Redirect sa bag-ong ngalan sa URL
        else:
            messages.error(request, 'There was an error updating your profile. Please check the form.')
            context = self.get_context_data()
            context['profile_form'] = profile_form
            context['user_form'] = user_form
            return render(request, self.template_name, context)