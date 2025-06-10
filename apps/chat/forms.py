from django import forms
from django.contrib.auth.models import User
from .models import InChargeProfile
from apps.church.models import Church
from .models import ChatMessage


class ChatMessageForm(forms.ModelForm):
    class Meta:
        model = ChatMessage
        fields = ['message']


class InChargeProfileForm(forms.ModelForm):
    user = forms.ModelChoiceField(queryset=User.objects.all(), label='User')
    church = forms.ModelChoiceField(
        queryset=Church.objects.all(), label='Church')

    class Meta:
        model = InChargeProfile
        fields = ['user', 'church']
