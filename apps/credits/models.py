import uuid
from django.db import models
from django.conf import settings


class CreditTransaction(models.Model):
    REASON_CHOICES = [
        ('signup_bonus', 'Signup Bonus'),
        ('admin_add', 'Admin Add'),
        ('optimization_used', 'Optimization Used'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='credit_transactions'
    )
    amount = models.IntegerField()
    reason = models.CharField(max_length=50, choices=REASON_CHOICES)
    admin_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.amount} credits - {self.reason} - {self.user.email}"