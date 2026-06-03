from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Task

@receiver(post_save, sender=Task)
def auto_add_user_to_project(sender, instance, created, **kwargs):
    # Если у задачи есть исполнитель, автоматически даем ему допуск к КИПу
    if instance.holder:
        main_project = instance.project.main_project
        if instance.holder not in main_project.allowed_Users.all():
            main_project.allowed_Users.add(instance.holder)