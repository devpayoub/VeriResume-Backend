from django.urls import path
from .views import CreditBalanceView, CreditTransactionsView, CreditRequestView

urlpatterns = [
    path('balance', CreditBalanceView.as_view(), name='credit-balance'),
    path('transactions', CreditTransactionsView.as_view(), name='credit-transactions'),
    path('request', CreditRequestView.as_view(), name='credit-request'),
]