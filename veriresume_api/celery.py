import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veriresume_api.settings')

app = Celery('veriresume_api')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()