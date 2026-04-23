from django.urls import path
from .views import VerifyTokenView, MeView

urlpatterns = [
    path('verify', VerifyTokenView.as_view(), name='verify'),
    path('me', MeView.as_view(), name='me'),
]