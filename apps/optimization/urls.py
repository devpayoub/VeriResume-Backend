from django.urls import path
from .views import (
    OptimizationStartView,
    OptimizationStatusView,
    OptimizationResultView,
    OptimizationAuditView,
    OptimizationHistoryView,
    OptimizationRetryView
)

urlpatterns = [
    path('', OptimizationStartView.as_view(), name='optimization-start'),
    path('history', OptimizationHistoryView.as_view(), name='optimization-history'),
    path('<uuid:session_id>/status', OptimizationStatusView.as_view(), name='optimization-status'),
    path('<uuid:session_id>/result', OptimizationResultView.as_view(), name='optimization-result'),
    path('<uuid:session_id>/audit', OptimizationAuditView.as_view(), name='optimization-audit'),
    path('<uuid:session_id>/retry/', OptimizationRetryView.as_view(), name='optimization-retry'),
]