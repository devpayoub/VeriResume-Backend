from rest_framework import serializers
from .models import CreditTransaction


class CreditTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditTransaction
        fields = ['id', 'amount', 'reason', 'admin_note', 'created_at']
        read_only_fields = ['id', 'amount', 'reason', 'admin_note', 'created_at']


class CreditRequestSerializer(serializers.Serializer):
    message = serializers.CharField(required=False, allow_blank=True)