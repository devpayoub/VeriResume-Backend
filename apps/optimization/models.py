import uuid
from django.db import models
from django.conf import settings


class Session(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='optimization_sessions'
    )
    resume = models.ForeignKey(
        'resumes.Resume',
        on_delete=models.CASCADE,
        related_name='sessions'
    )
    job_description_text = models.TextField()
    target_job_title = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    credits_deducted = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Session {self.id} - {self.status}"


class OptimizedResult(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.OneToOneField(
        Session,
        on_delete=models.CASCADE,
        related_name='result'
    )
    rewritten_text = models.TextField()
    download_path = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Result for Session {self.session_id}"


class AuditTrail(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    optimized_result = models.ForeignKey(
        OptimizedResult,
        on_delete=models.CASCADE,
        related_name='audit_trails'
    )
    original_sentence = models.TextField(blank=True)
    optimized_sentence = models.TextField()
    is_honest = models.BooleanField(default=True)
    confidence_score = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"Audit {self.id} - Honest: {self.is_honest}"