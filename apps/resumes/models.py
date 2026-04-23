import uuid
from django.db import models
from django.conf import settings


class Resume(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='resumes'
    )
    filename = models.CharField(max_length=255)
    parsed_text = models.TextField(blank=True)
    file_path = models.CharField(max_length=500, blank=True)
    word_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.filename} - {self.user.email}"