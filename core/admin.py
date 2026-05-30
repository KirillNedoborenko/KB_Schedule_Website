from django.contrib import admin
from .models import MainProject,Project,Task

@admin.register(MainProject)
class MainProjectAdmin(admin.ModelAdmin):
    list_display = ('mp_id','mp_name')
    filter_horizontal = ['allowed_Users']

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('pr_id','pr_number', 'pr_name', 'status', 'main_project')
    list_filter = ('status', 'main_project')

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('task_id','task_name','holder','start_date','end_date','workload','project')
    list_filter = ('project','holder')