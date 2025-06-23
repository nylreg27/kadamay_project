# apps/account/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import ListView, TemplateView, View
from .models import Church, ChatMessage
from .forms import ChatMessageForm
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from .forms import InChargeProfileForm


# 1. List all churches with chat rooms (or just all churches)


@method_decorator(login_required, name='dispatch')
class ChurchChatListView(ListView):
    model = Church
    template_name = 'chat/church_list.html'
    context_object_name = 'churches'

# 2. Chat room detail view for a specific church


@method_decorator(login_required, name='dispatch')
class ChatView(TemplateView):
    template_name = 'chat/chat_room.html'

    def dispatch(self, request, *args, **kwargs):
        church_id = kwargs.get('church_id')
        church = get_object_or_404(Church, id=church_id)

        # ✅ Admins can access all
        if request.user.is_superuser or request.user.groups.filter(name='Admin').exists():
            return super().dispatch(request, *args, **kwargs)

        # ✅ InCharge can only access their assigned church
        if request.user.groups.filter(name='Church_In_Charge').exists():
            try:
                if request.user.inchargeprofile.church.id != church.id:
                    return render(request, 'chat/access_denied.html', {
                        'message': "You are not assigned to this church. Access denied."
                    })
            except:
                return render(request, 'chat/access_denied.html', {
                    'message': "No church assignment found for this user."
                })

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        church_id = self.kwargs.get('church_id')
        church = get_object_or_404(Church, id=church_id)

        context['church'] = church
        context['messages'] = ChatMessage.objects.filter(
            church=church).order_by('-sent_at')[:50][::-1]
        context['messages_url'] = reverse(
            'chat:get_messages', args=[church.id])
        return context


# 3. API endpoint: get messages JSON for AJAX calls


@method_decorator(login_required, name='dispatch')
class GetMessagesView(View):
    def get(self, request, church_id):
        last_message_id = request.GET.get('last_message_id', 0)
        messages = ChatMessage.objects.filter(
            church_id=church_id, id__gt=last_message_id).order_by('timestamp')

        data = []
        for msg in messages:
            data.append({
                'id': msg.id,
                'user': msg.user.username,
                'message': msg.message,
                'timestamp': msg.sent_at.isoformat(),
            })

        return JsonResponse({'messages': data})

# saff


@staff_member_required
def create_incharge_profile_view(request):
    if request.method == 'POST':
        form = InChargeProfileForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin:index')  # or any success page
    else:
        form = InChargeProfileForm()
    return render(request, 'chat/create_incharge_profile.html', {'form': form})
