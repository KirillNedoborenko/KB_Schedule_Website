from django.contrib import admin
from django.urls import path
from core.views import global_kb_Schedule,main_project_detail
from core.views import create_sub_project,create_new_task,delete_task,delete_project
from core.views import update_task,update_project
from core.views import login_user,logout_user,dashboard_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('',global_kb_Schedule, name='global_kb_timeline'),
    path('project/<int:mp_id>/', main_project_detail, name='project_tab_detail'),
    path('create_sub_project',create_sub_project,name='create_sub_project'),
    path('create_new_task',create_new_task,name='create_new_task'),
    path('delete_task',delete_task,name='delete_task'),
    path('delete_project',delete_project,name='delete_project'),
    path('update_task',update_task,name='update_task'),
    path('update_project',update_project,name='update_project'),
    path('login/',login_user,name='login_user'),
    path('logout/',logout_user,name='logout_user'),
    path('dashboard/',dashboard_view,name='dashboard')
]
