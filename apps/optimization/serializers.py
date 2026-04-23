from rest_framework import serializers
from .models import Session, OptimizedResult, AuditTrail


class SessionCreateSerializer(serializers.Serializer):
    resume_id = serializers.UUIDField()
    job_description_text = serializers.CharField()
    target_job_title = serializers.CharField(required=False, allow_blank=True)


class SessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Session
        fields = [
            'id', 'resume_id', 'job_description_text', 'target_job_title',
            'status', 'credits_deducted', 'error_message', 'created_at', 'completed_at'
        ]
        read_only_fields = ['id', 'status', 'credits_deducted', 'error_message', 'created_at', 'completed_at']


class OptimizedResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = OptimizedResult
        fields = ['id', 'rewritten_text', 'download_path', 'created_at']
        read_only_fields = ['id', 'rewritten_text', 'download_path', 'created_at']


class AuditTrailSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditTrail
        fields = ['id', 'original_sentence', 'optimized_sentence', 'is_honest', 'confidence_score']
        read_only_fields = ['id', 'original_sentence', 'optimized_sentence', 'is_honest', 'confidence_score']


class SessionDetailSerializer(serializers.ModelSerializer):
    result = OptimizedResultSerializer(read_only=True)
    audit_trails = AuditTrailSerializer(many=True, read_only=True)

    class Meta:
        model = Session
        fields = [
            'id', 'resume_id', 'job_description_text', 'target_job_title',
            'status', 'credits_deducted', 'error_message', 'created_at', 'completed_at',
            'result', 'audit_trails'
        ]
        read_only_fields = ['id', 'status', 'credits_deducted', 'error_message', 'created_at', 'completed_at']