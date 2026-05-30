from django.db import models
from django.contrib.auth.models import User

class MainProject(models.Model):
    mp_id = models.AutoField(primary_key=True)
    mp_name = models.TextField(verbose_name="Название КИПА")

    allowed_Users = models.ManyToManyField(User,related_name="allowed_main_projects",
                                           blank=True,verbose_name = "Доступ сотрудников")

    def __str__(self):
        return self.mp_name


class Project(models.Model):
    pr_id = models.AutoField(primary_key = True)
    pr_number = models.TextField(verbose_name="Номер проекта")
    pr_name = models.TextField(verbose_name="Название проекта",null=True,blank=True)
    volume = models.DecimalField(max_digits=10,decimal_places=2,null=True,
                                 blank=True,verbose_name="Обьём")
    status = models.TextField(null=True,blank=True,verbose_name="Статус")
    main_project = models.ForeignKey(MainProject,on_delete=models.CASCADE,
                                     related_name="projects",db_column="main_project_id")

    def __str__(self):
        return f"{self.pr_number} - {self.pr_name if self.pr_name else ''}"


class Task(models.Model):
    task_id = models.AutoField(primary_key=True)
    project = models.ForeignKey(Project,on_delete=models.CASCADE,related_name="tasks",
                                db_column="project_id")
    holder = models.ForeignKey(User,on_delete=models.SET_NULL,null=True,blank=True,
                               related_name="tasks",db_column="holder_id",
                               verbose_name="Исполнитель")
    start_date = models.DateField(null=True,blank=True,verbose_name="Дата начала")
    end_date = models.DateField(null=True,blank=True,verbose_name="Дата окончания")
    workload = models.DecimalField(max_digits=10,decimal_places=2,null=True,
                                   blank=True,verbose_name="Трудоёмкость")
    task_name = models.TextField(verbose_name="Название задачи")
    task_comment = models.TextField(null=True,blank=True,verbose_name="Комментарий")

    def __str__(self):
        return self.task_name