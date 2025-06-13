# apps/payment/serializers.py
from rest_framework import serializers
from .models import ContributionType


class ContributionTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContributionType
        fields = '__all__'
