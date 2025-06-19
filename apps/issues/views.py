from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from apps.issues.models import IssueReport

# Admin-only view mixin (checks if user is superuser)


class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser

# 1. Admin list: all issue report


class IssueReportListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = IssueReport
    template_name = 'issues/issue_list.html'
    context_object_name = 'issues'
    paginate_by = 20  # Pagination if you want

# 2. User’s own issues list


class UserIssueListView(LoginRequiredMixin, ListView):
    model = IssueReport
    template_name = 'issues/user_issue_list.html'
    context_object_name = 'issues'
    paginate_by = 20

    def get_queryset(self):
        return IssueReport.objects.filter(reporter=self.request.user).order_by('-created_at')


# 3. Create a new issue report
class IssueReportCreateView(LoginRequiredMixin, CreateView):
    model = IssueReport
    # Adjust fields as per your model
    fields = ['title', 'description', 'priority', 'status']
    template_name = 'issues/issue_form.html'
    success_url = reverse_lazy('issues:user_issue_list')

    def form_valid(self, form):
        # Set reporter to the logged-in user automatically
        form.instance.reporter = self.request.user
        return super().form_valid(form)

# 4. View issue report details


class IssueReportDetailView(LoginRequiredMixin, DetailView):
    model = IssueReport
    template_name = 'issues/issue_detail.html'
    context_object_name = 'issue'

# 5. Update issue report


class IssueReportUpdateView(LoginRequiredMixin, UpdateView):
    model = IssueReport
    fields = ['title', 'description', 'priority', 'status']  # Adjust as needed
    template_name = 'issues/issue_form.html'
    success_url = reverse_lazy('issues:user_issue_list')

    def get_queryset(self):
        # Users can only update their own issues; admins can update all
        if self.request.user.is_superuser:
            return IssueReport.objects.all()
        return IssueReport.objects.filter(reporter=self.request.user)
