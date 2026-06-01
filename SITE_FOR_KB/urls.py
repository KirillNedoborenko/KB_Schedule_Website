from django.contrib import admin
from django.urls import path
from core.views import global_kb_Schedule,main_project_detail

urlpatterns = [
    path('admin/', admin.site.urls),
    path('',global_kb_Schedule, name='global_kb_timeline'),
    path('project/<int:mp_id>/', main_project_detail, name='project_tab_detail'),
]
