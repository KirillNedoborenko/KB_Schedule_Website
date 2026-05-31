from django.contrib import admin
from django.urls import path
from core.views import global_kb_Schedule

urlpatterns = [
    path('admin/', admin.site.urls),
    path('',global_kb_Schedule, name='global_kb_timeline'),
]
