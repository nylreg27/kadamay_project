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

# 🔐 Mixins (Keep these - crucial for permissions)


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

# 👮‍♂️ User Management (Admin Only) - Class-Based Views for consistency


class UserListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = User
    template_name = 'account/user_list.html'
    context_object_name = 'users'
    paginate_by = 20

    def get_queryset(self):
        # Exclude superuser from this list if you want to prevent superuser from deleting self
        # Or you can add logic in the template to disable delete/edit for superuser if needed.
        return User.objects.order_by('username')


class UserCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = User
    form_class = StyledUserCreationForm
    template_name = 'account/user_form.html'
    success_url = reverse_lazy('account:user_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Pass page_title to template
        context['page_title'] = 'Create New User'
        return context

    def form_valid(self, form):
        user = form.save()  # Save the user and their profile (handled by form's save method)
        messages.success(
            self.request, f"User '{user.username}' created successfully!")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(
            self.request, "Error creating user. Please check the form.")
        return super().form_invalid(form)


class UserUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = User
    # Use UserUpdateForm if you created one, otherwise specify fields directly
    # from your previous forms.py, I recommend using a UserUpdateForm if you want to customize it.
    # For now, I'll use the fields from your previous views.
    fields = ['username', 'email', 'first_name',
              'last_name', 'is_active', 'is_staff', 'is_superuser']
    template_name = 'account/user_form.html'
    success_url = reverse_lazy('account:user_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Update User'  # Pass page_title to template
        return context

    def form_valid(self, form):
        messages.success(
            self.request, f"User '{self.object.username}' updated successfully!")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(
            self.request, "Error updating user. Please check the form.")
        return super().form_invalid(form)


class UserDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = User
    template_name = 'account/user_confirm_delete.html'
    success_url = reverse_lazy('account:user_list')
    # Better context name for the user being deleted
    context_object_name = 'target_user'

    def form_valid(self, form):
        messages.success(
            self.request, f"User '{self.object.username}' deleted successfully!")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Error deleting user.")
        return super().form_invalid(form)

# 🔁 Role Management (Using Django's Group model - useful for broader permissions)


class UserRoleForm(forms.Form):
    # This form now maps to Django's built-in Group model
    role = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        label='Assign Role',
        widget=forms.Select(attrs={
                            'class': 'select select-bordered w-full uppercase focus:outline-none focus:ring-2 focus:ring-primary select-xs text-xs'})
    )


class UserRoleAssignView(LoginRequiredMixin, AdminRequiredMixin, View):
    template_name = 'account/user_role_form.html'

    def get(self, request, user_id):
        user = get_object_or_404(User, pk=user_id)
        form = UserRoleForm()
        messages.info(
            request, f"Current roles for {user.username}: {', '.join([g.name for g in user.groups.all()]) or 'None'}")
        return render(request, self.template_name, {'form': form, 'user': user, 'page_title': f'Assign Role to {user.username}'})

    def post(self, request, user_id):
        user = get_object_or_404(User, pk=user_id)
        form = UserRoleForm(request.POST)
        if form.is_valid():
            # Clear existing groups and add the new one for simplicity in this example
            user.groups.clear()
            user.groups.add(form.cleaned_data['role'])
            user.save()
            messages.success(
                request, f"Role assigned to '{user.username}' successfully!")
            return redirect('account:user_list')
        messages.error(
            request, "Failed to assign role. Please check the form.")
        return render(request, self.template_name, {'form': form, 'user': user, 'page_title': f'Assign Role to {user.username}'})


class UserRoleDeleteView(LoginRequiredMixin, AdminRequiredMixin, View):
    def post(self, request, user_id):
        user = get_object_or_404(User, pk=user_id)
        user.groups.clear()  # Removes all groups from the user
        user.save()
        messages.success(
            request, f"Roles cleared for '{user.username}' successfully!")
        return redirect('account:user_list')

# User Registration View (for new users to sign up)


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


class ProfileSettingsView(LoginRequiredMixin, View):
    template_name = 'account/profile_settings.html'

    def get_context_data(self, **kwargs):
        context = {}
        try:
            profile = self.request.user.profile
        except Profile.DoesNotExist:
            profile = Profile.objects.create(user=self.request.user)

        context['profile_form'] = ProfileThemeForm(instance=profile)
        # Assuming UserDetailsForm handles first_name, last_name, email
        context['user_form'] = UserDetailsForm(instance=self.request.user)

        context['user_status'] = "Active" if self.request.user.is_active else "Inactive"

        user_type_list = []
        if self.request.user.is_superuser:
            user_type_list.append("Admin (Superuser)")
        if self.request.user.is_staff:
            user_type_list.append("Staff")
        # Add roles from custom Profile model if it has a 'role' field
        if hasattr(self.request.user, 'profile') and self.request.user.profile.role:
            user_type_list.append(self.request.user.profile.get_role_display())
        # Add roles from Django Groups
        for group in self.request.user.groups.all():
            user_type_list.append(group.name)

        context['user_type'] = ", ".join(
            sorted(list(set(user_type_list)))) if user_type_list else "Regular User"
        # Add page title for the template
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

        profile_form = ProfileThemeForm(
            request.POST, request.FILES, instance=profile)
        user_form = UserDetailsForm(request.POST, instance=request.user)

        if profile_form.is_valid() and user_form.is_valid():
            profile_form.save()
            user_form.save()
            messages.success(
                request, 'Your profile settings have been updated successfully!')
            # Redirect to the profile settings page itself
            return redirect('account:profile')
        else:
            messages.error(
                request, 'There was an error updating your profile. Please check the form.')
            context = self.get_context_data()
            # Pass back the forms with errors
            context['profile_form'] = profile_form
            context['user_form'] = user_form
            return render(request, self.template_name, context)

# 👤 Create In-Charge User (Admin Only)


class UserCreateInchargeView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = User
    form_class = StyledUserCreationForm  # Atong gamiton ang existing form
    # Atong gamiton ang existing user form template
    template_name = 'account/user_form.html'
    # Human ma-create, balik sa user list
    success_url = reverse_lazy('account:user_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Kini ang title nga makita sa template
        context['page_title'] = 'Create New In-Charge User'
        return context

    def form_valid(self, form):
        # Gamiton nato ang transaction para sigurado nga magkasinabtanay ang user creation ug group assignment
        with transaction.atomic():
            # Ayaw sa i-save fully para ma-modify pa nato
            user = form.save(commit=False)
            user.is_staff = True  # Maghatag ta og staff access para makalog-in sa admin panel
            user.save()  # I-save na ang user sa database

            # Pangitaon o buhaton ang 'Incharge' Group. Importante nga consistent ang spelling!
            incharge_group, created = Group.objects.get_or_create(
                name='Incharge')
            # Id-dagan ang user sa 'Incharge' group
            user.groups.add(incharge_group)

            messages.success(
                self.request,
                f"In-Charge user '{user.username}' created and assigned to 'Incharge' role successfully!"
            )
        # Redirect ngadto sa success_url
        return redirect(self.get_success_url())

    def form_invalid(self, form):
        messages.error(
            self.request,
            "Error creating In-Charge user. Please check the form."
        )
        return super().form_invalid(form)
