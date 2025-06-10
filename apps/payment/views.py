from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import Payment, ContributionType  # Make sure both models exist

# ---- ContributionType Views ----
class ContributionTypeListView(ListView):
    model = ContributionType
    template_name = 'payment/contributiontype_list.html'

class ContributionTypeCreateView(CreateView):
    model = ContributionType
    fields = '__all__'
    template_name = 'payment/contributiontype_form.html'
    success_url = reverse_lazy('payment:contribution_type_list')

class ContributionTypeDetailView(DetailView):
    model = ContributionType
    template_name = 'payment/contributiontype_detail.html'

class ContributionTypeUpdateView(UpdateView):
    model = ContributionType
    fields = '__all__'
    template_name = 'payment/contributiontype_form.html'
    success_url = reverse_lazy('payment:contribution_type_list')

class ContributionTypeDeleteView(DeleteView):
    model = ContributionType
    template_name = 'payment/contributiontype_confirm_delete.html'
    success_url = reverse_lazy('payment:contribution_type_list')

# ---- Payment Views ----
class PaymentListView(ListView):
    model = Payment
    template_name = 'payment/payment_list.html'

    def get_queryset(self):
        individual_id = self.kwargs.get('individual_id')
        if individual_id:
            return Payment.objects.filter(individual_id=individual_id)
        return Payment.objects.all()

class PaymentCreateView(CreateView):
    model = Payment
    fields = '__all__'
    template_name = 'payment/payment_form.html'
    success_url = reverse_lazy('payment:payment_list')

    def get_initial(self):
        individual_id = self.kwargs.get('individual_id')
        if individual_id:
            return {'individual_id': individual_id}
        return super().get_initial()

class PaymentDetailView(DetailView):
    model = Payment
    template_name = 'payment/payment_detail.html'

class PaymentUpdateView(UpdateView):
    model = Payment
    fields = '__all__'
    template_name = 'payment/payment_form.html'
    success_url = reverse_lazy('payment:payment_list')

class PaymentDeleteView(DeleteView):
    model = Payment
    template_name = 'payment/payment_confirm_delete.html'
    success_url = reverse_lazy('payment:payment_list')
