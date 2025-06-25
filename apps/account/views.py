# apps/account/views.py (Corrected Version)

from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.views.generic import (
    ListView, CreateView, UpdateView, DeleteView, View # Removed DetailView as it's not explicitly used for ProfileDetail
)
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.contrib import messages
from django import forms # For generic forms, but specific forms are imported from .forms
from django.db import transaction

# Import Models and Forms from the current app
from .models import Profile, UserChurch # Include UserChurch if you still plan to use it
from .forms import ProfileThemeForm, UserDetailsForm, StyledUserCreationForm, UserLoginForm

User = get_user_model()

# 🔐 Mixins (Crucial for permissions)
class ProfileOwnerMixin(UserPassesTestMixin):
    """
    Mixin to ensure a user can only access/modify their own profile,
    unless they are a superuser.
    """
    def test_func(self):
        # For Profile views, ensure the requesting user owns the profile or is superuser
        profile_pk = self.kwargs.get('pk')
        if profile_pk:
            profile = get_object_or_404(Profile, pk=profile_pk)
            return profile.user == self.request.user or self.request.user.is_superuser
        # If no PK (e.g., accessing own profile without PK in URL), just check authentication
        return self.request.user.is_authenticated

    def handle_no_permission(self):
        messages.warning(self.request, "You do not have permission to access this profile.")
        return redirect(reverse_lazy('account:profile')) # Redirect to own profile


class AdminRequiredMixin(UserPassesTestMixin):
    """
    Mixin to restrict access to superusers only.
    """
    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        messages.error(self.request, "You must be an administrator to access this page.")
        return redirect(reverse_lazy('account:profile')) # Or redirect to a custom permission denied page

# 👮‍♂️ User Management (Admin Only) - Class-Based Views for consistency

class UserListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = User
    template_name = 'account/user_list.html'
    context_object_name = 'users'
    paginate_by = 20

    def get_queryset(self):
        # Order users by username for consistent display
        return User.objects.order_by('username')

class UserCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = User
    form_class = StyledUserCreationForm
    template_name = 'account/user_form.html'
    success_url = reverse_lazy('account:user_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Create New User'
        return context

    def form_valid(self, form):
        # The form's save method (StyledUserCreationForm.save()) handles user and profile creation/role assignment
        user = form.save()
        messages.success(self.request, f"User '{user.username}' created successfully!")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Error creating user. Please check the form.")
        return super().form_invalid(form)


class UserUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = User
    # Use UserDetailsForm for user details and manage roles separately.
    # If you need to update is_active, is_staff, is_superuser, explicitly include them here.
    fields = ['email', 'first_name', 'last_name', 'is_active', 'is_staff', 'is_superuser']
    template_name = 'account/user_form.html'
    success_url = reverse_lazy('account:user_list')
    context_object_name = 'target_user' # Renamed from 'user' to avoid confusion with request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Update User: {self.object.username}'
        # Pass the profile role for display in the template if needed
        context['current_profile_role'] = self.object.profile.get_role_display() if hasattr(self.object, 'profile') else 'N/A'
        
        # If the username field is in the form, you might want to make it readonly
        # This is typically handled by the form's __init__ method for UserUpdateForm,
        # but since we are using direct fields, you might need to control this in the template.
        # Or you could define a separate UserUpdateAdminForm.
        return context

    def form_valid(self, form):
        messages.success(self.request, f"User '{self.object.username}' updated successfully!")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Error updating user. Please check the form.")
        return super().form_invalid(form)


class UserDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = User
    template_name = 'account/user_confirm_delete.html'
    success_url = reverse_lazy('account:user_list')
    context_object_name = 'target_user' # Ensure consistent context object name

    def form_valid(self, form):
        messages.success(self.request, f"User '{self.object.username}' deleted successfully!")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Error deleting user.")
        return super().form_invalid(form)

# 🔁 Role Management (Using Django's Group model - useful for broader permissions)

# UserRoleForm (kept as is, it's defined in forms.py and used here)

class UserRoleAssignView(LoginRequiredMixin, AdminRequiredMixin, View):
    template_name = 'account/user_role_form.html'

    def get(self, request, user_id):
        user = get_object_or_404(User, pk=user_id)
        form = forms.UserRoleForm() # Use the form from forms.py
        messages.info(request, f"Current roles for {user.username}: {', '.join([g.name for g in user.groups.all()]) or 'None'}")
        return render(request, self.template_name, {'form': form, 'target_user': user, 'page_title': f'Assign Role to {user.username}'})

    def post(self, request, user_id):
        user = get_object_or_404(User, pk=user_id)
        form = forms.UserRoleForm(request.POST)
        if form.is_valid():
            # Clear existing groups and add the new one for simplicity in this example
            user.groups.clear()
            user.groups.add(form.cleaned_data['role'])
            user.save()
            messages.success(request, f"Role assigned to '{user.username}' successfully!")
            return redirect('account:user_list')
        messages.error(request, "Failed to assign role. Please check the form.")
        return render(request, self.template_name, {'form': form, 'target_user': user, 'page_title': f'Assign Role to {user.username}'})


class UserRoleDeleteView(LoginRequiredMixin, AdminRequiredMixin, View):
    def post(self, request, user_id):
        user = get_object_or_404(User, pk=user_id)
        user.groups.clear()  # Removes all groups from the user
        user.save()
        messages.success(request, f"Roles cleared for '{user.username}' successfully!")
        return redirect('account:user_list')

# User Registration View (for new users to sign up)

class RegisterView(CreateView):
    template_name = 'account/register.html' # Changed template path to 'account/register.html'
    form_class = StyledUserCreationForm
    success_url = reverse_lazy('account:login')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Account created successfully. Please log in.")
        return response

    def form_invalid(self, form):
        messages.error(self.request, "There was an error in your registration. Please check the form.")
        return super().form_invalid(form)

# --- PROFILE SETTINGS VIEW (Ang atong gigamit karon) ---
# This view now correctly allows updating both Profile and User details.

class ProfileSettingsView(LoginRequiredMixin, View):
    template_name = 'account/profile_settings.html'

    def get_context_data(self, **kwargs):
        context = {}
        # Ensure profile exists, create if not (signal should handle this too, but for safety)
        try:
            profile = self.request.user.profile
        except Profile.DoesNotExist:
            profile = Profile.objects.create(user=self.request.user)

        context['profile_form'] = ProfileThemeForm(instance=profile)
        # UserDetailsForm should be for first_name, last_name, email (editable)
        context['user_form'] = UserDetailsForm(instance=self.request.user)

        context['user_status'] = "Active" if self.request.user.is_active else "Inactive"

        user_type_list = []
        if self.request.user.is_superuser:
            user_type_list.append("Admin (Superuser)")
        if self.request.user.is_staff:
            user_type_list.append("Staff")
        
        # Add roles from custom Profile model field
        if hasattr(self.request.user, 'profile') and self.request.user.profile.role:
            # Ensure it's not a duplicate if group name is the same as profile role
            if self.request.user.profile.get_role_display() not in user_type_list:
                user_type_list.append(self.request.user.profile.get_role_display())
        
        # Add roles from Django Groups
        for group in self.request.user.groups.all():
            if group.name not in user_type_list: # Avoid duplicates
                user_type_list.append(group.name)

        context['user_type'] = ", ".join(sorted(list(set(user_type_list)))) if user_type_list else "Regular User"
        context['page_title'] = 'Profile Settings'
        
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
            return redirect('account:profile') # Redirect to the profile settings page itself
        else:
            messages.error(request, 'There was an error updating your profile. Please check the form.')
            context = self.get_context_data() # Re-call to get fresh forms
            context['profile_form'] = profile_form # Pass back forms with errors
            context['user_form'] = user_form
            return render(request, self.template_name, context)

# 👤 Create In-Charge User (Admin Only)

class UserCreateInchargeView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = User
    form_class = StyledUserCreationForm # Use the StyledUserCreationForm for consistency
    template_name = 'account/user_form.html'
    success_url = reverse_lazy('account:user_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Create New In-Charge User'
        # Set the role field's initial value to IN_CHARGE for this specific form
        context['form'].fields['role'].initial = Profile.IN_CHARGE
        # Optionally, make the role field read-only or hidden if it's always 'IN_CHARGE'
        # context['form'].fields['role'].widget = forms.HiddenInput()
        return context

    def form_valid(self, form):
        response = super().form_valid(form) # Save the user and their profile via StyledUserCreationForm.save()

        user = self.object # The newly created user instance
        
        # Ensure the user is marked as staff if they are In-Charge
        if not user.is_staff:
            user.is_staff = True
            user.save(update_fields=['is_staff'])

        # Assign to 'In-Charge' group
        incharge_group, created = Group.objects.get_or_create(name='In-Charge') # Use 'In-Charge' (consistent spelling)
        user.groups.add(incharge_group)

        messages.success(
            self.request,
            f"In-Charge user '{user.username}' created and assigned to 'In-Charge' role successfully!"
        )
        return response

    def form_invalid(self, form):
        messages.error(
            self.request,
            "Error creating In-Charge user. Please check the form."
        )
        return super().form_invalid(form)

# Profile Detail View (for displaying own profile - for user, not admin list)
class UserProfileDetailView(LoginRequiredMixin, ProfileOwnerMixin, View):
    template_name = 'account/profile_detail.html'

    def get(self, request, pk=None, *args, **kwargs):
        # If PK is provided, ensure it's the owner's profile or superuser access.
        # Otherwise, assume request.user's profile.
        if pk:
            profile = get_object_or_404(Profile, pk=pk)
            # ProfileOwnerMixin already handles permission check
        else:
            profile = request.user.profile # Access current user's profile

        context = {
            'profile': profile,
            'user_obj': profile.user, # The related User object
            'page_title': f"{profile.user.username}'s Profile"
        }
        return render(request, self.template_name, context)

# Profile Create View (if users can create their own profile separate from user creation)
# Often, profile creation is handled automatically via signals or within user creation.
# If you intend for admins to manually create profiles for existing users, this view is useful.
class ProfileCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = Profile
    form_class = ProfileThemeForm # Or a more comprehensive ProfileForm if needed
    template_name = 'account/profile_form.html'
    success_url = reverse_lazy('account:user_list') # Redirect to user list after creating profile

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Create New Profile'
        return context

    def form_valid(self, form):
        # You might need to select an existing user for this profile if not linked by form.
        # For simplicity, if this is for creating a profile for an already existing user,
        # you might add a 'user' field to the form, or handle it in the view.
        # For now, let's assume it's for an existing user whose profile doesn't exist yet.
        # This view's purpose needs to be clearly defined relative to StyledUserCreationForm.
        # If StyledUserCreationForm creates Profile, then this view is for *manual* profile creation for existing users.
        messages.success(self.request, "Profile created successfully!")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Error creating profile. Please check the form.")
        return super().form_invalid(form)

# Profile Update View (if separate from ProfileSettingsView, e.g., admin updates specific profile)
# If ProfileSettingsView is the primary update, this might be redundant.
# For now, let's assume ProfileSettingsView handles own user's profile updates.

# Profile Delete View (for admin to delete a profile, separate from user deletion)
class ProfileDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = Profile
    template_name = 'account/profile_confirm_delete.html'
    context_object_name = 'profile'
    success_url = reverse_lazy('account:user_list') # Redirect to user list after deleting profile

    def form_valid(self, form):
        messages.success(self.request, f"Profile for '{self.object.user.username}' deleted successfully!")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Error deleting profile.")
        return super().form_invalid(form)

