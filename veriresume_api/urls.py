"""
URL configuration for veriresume_api project.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/auth/', include('apps.accounts.urls')),
    path('api/v1/credits/', include('apps.credits.urls')),
    path('api/v1/resumes/', include('apps.resumes.urls')),
    path('api/v1/optimize/', include('apps.optimization.urls')),
]