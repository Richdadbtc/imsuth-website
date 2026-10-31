from rest_framework import serializers

from .models import ApprovalRequest, ReconciliationBatch, ReconciliationItem


class ApprovalRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApprovalRequest
        fields = "__all__"
        read_only_fields = ("id", "status", "created_at", "updated_at")


class ReconciliationItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReconciliationItem
        fields = "__all__"


class ReconciliationBatchSerializer(serializers.ModelSerializer):
    items = ReconciliationItemSerializer(many=True, read_only=True)

    class Meta:
        model = ReconciliationBatch
        fields = "__all__"
