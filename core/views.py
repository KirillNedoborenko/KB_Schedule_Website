import json
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from .models import MainProject,Task,Project
from datetime import datetime,timedelta
from django.contrib.auth import authenticate,login,logout
from django.shortcuts import render, redirect
import traceback

@login_required
def global_kb_Schedule(request):
    is_kb_boss = request.user.groups.filter(name='Руководители КБ').exists()
    if request.user.is_superuser:
        user_projects = MainProject.objects.all()
    else:
        user_projects = MainProject.objects.filter(allowed_Users=request.user)

    if not user_projects.exists():
        return redirect('dashboard')
    
    users_set = User.objects.filter(is_superuser=False).order_by('username')
    tasks_set = Task.objects.all().select_related('holder','project__main_project')

    raw_events = []
    min_date = None
    max_date = None
    workload_sum = 0

    for t in tasks_set:
        if t.start_date and t.workload and t.holder:
            days_to_add = int(t.workload)
            end_date = t.start_date + timedelta(days=days_to_add)
            workload_sum+=days_to_add

            raw_events.append({
                'holder_id': t.holder.id,
                'task_name': t.task_name,
                'project_name': t.project.pr_name,
                'start': t.start_date,
                'workload': days_to_add,
                'end': t.start_date + timedelta(days = days_to_add),
            })

            if min_date is None or t.start_date < min_date: min_date = t.start_date
            if max_date is None or t.start_date > max_date: max_date = t.start_date
    
    if not min_date:
        min_date = max_date = datetime.now().date()

    max_date+=timedelta(days=workload_sum)

    days_max_count = (max_date - min_date).days + 10

    timeline_by_user = {}
    final_processed_bars = []

    for user in users_set:
        user_tasks = [t for t in raw_events if t['holder_id']==user.id]
        user_tasks.sort(key=lambda x: x['start'], reverse = True)

        allowed_dates = [min_date + timedelta(days=i) for i in range(days_max_count)]

        for task in user_tasks:
            days_placed = 0
            current_date = task['start']
            task_occupied_dates = []

            while days_placed < task['workload'] and allowed_dates:
                if current_date in allowed_dates:
                    task_occupied_dates.append(current_date)

                    allowed_dates.remove(current_date)
                    days_placed+=1
                    current_date += timedelta(days=1)
                else:
                    current_date += timedelta(days=1)
        
            if task_occupied_dates:
                task_occupied_dates.sort()

                start_seg = task_occupied_dates[0]
                prev_date = task_occupied_dates[0]

                for d in task_occupied_dates[1:]:
                    if d != prev_date + timedelta(days=1):
                        final_processed_bars.append({
                            'username': user.username,
                            'task_name': task['task_name'],
                            'project_name': task['project_name'],
                            'start': start_seg,
                            'end': prev_date + timedelta(days=1)
                        })
                        start_seg = d
                    prev_date = d
                
                final_processed_bars.append({
                    'username': user.username,
                    'task_name': task['task_name'],
                    'project_name': task['project_name'],
                    'start': start_seg,
                    'end': prev_date + timedelta(days=1)
                })
    
    if final_processed_bars:
        max_date = max(b['end'] for b in final_processed_bars)
    else:
        max_date = min_date + timedelta(days=1)
    
    total_days = (max_date - min_date).days or 1

    for user in users_set:
        user_bars = [b for b in final_processed_bars if b['username']==user.username]
        chunks = []

        for bar in user_bars:
            left_days = (bar['start'] - min_date).days
            duration_days = (bar['end'] - bar['start']).days

            chunks.append({
                'task_name': bar['task_name'],
                'project_name': bar['project_name'],
                'left': round((left_days/total_days) * 100,2),
                'width': round((duration_days / total_days) * 100,2),
                'is_active': True
            })
        
        chunks.sort(key=lambda x: x['left'])
        timeline_by_user[user.username] = chunks

    all_dates = [min_date + timedelta(days=i) for i in range(total_days)]
    
    return render(request,'core/global_kb_timeline.html',{
        'timeline_by_user': timeline_by_user,
        'min_date': min_date,
        'max_date': max_date,
        'all_dates': all_dates,
        'total_days': total_days,
    })

@login_required
def main_project_detail(request, mp_id):
    main_project = get_object_or_404(MainProject, mp_id=mp_id)

    if not request.user.is_superuser and not request.user.has_perm('core.view_all_main_projects') \
       and request.user not in main_project.allowed_Users.all():
       raise PermissionError("У вас нет прав доступа к этой вкладке")

    sub_projects = main_project.projects.all()
    tasks = Task.objects.filter(project__main_project=main_project).select_related('holder','project')

    return render(request, 'core/project_detail.html',{
        'main_project': main_project,
        'sub_projects': sub_projects,
        'tasks': tasks,
        'current_tab': main_project.mp_id
    })

@login_required
def create_sub_project(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            mp_id = data.get('main_project_id')
            pr_number = data.get('pr_number','').strip()
            pr_name = data.get('pr_name','').strip()
            volume = data.get('volume','').strip()
            status = data.get('status','').strip()

            if not pr_number or not pr_name:
                return JsonResponse({'status': 'error','message': 'Номер и наименование проекта обязательны!!!'},status=400)

            main_project = get_object_or_404(MainProject, mp_id=mp_id)
            volume_decimal = float(volume) if volume else None

            new_project = Project.objects.create(
                main_project=main_project,
                pr_number=pr_number,
                pr_name=pr_name,
                volume=volume_decimal,
                status=status if status else "В работе"
            )

            return JsonResponse({
                'status': 'success',
                'message': 'Проект успешно добавлен!',
                'project_id': new_project.pr_id
            })
        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            print("КРАШ НА БЭКЕНДЕ:", error_msg) # Напечатает в терминал
            traceback.print_exc()               # Выведет лог со строкой в терминал
            
            # Возвращаем статус 200, чтобы JavaScript гарантированно ПРОЧИТАЛ эту ошибку,
            # а не выкидывал стандартную заглушку 500!
            return JsonResponse({'status': 'error', 'message': error_msg}, status=200)

    return JsonResponse({'status': 'error','message': 'Неверный метод запроса!!!'},status=400)

@login_required
def create_new_task(request):
    date_template = "%d.%m.%Y"
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            project_id = data.get('project_id')
            project = get_object_or_404(Project,pr_id=project_id)
            main_project = project.main_project

            if not request.user.is_superuser and request.user not in main_project.allowed_Users.all():
                return JsonResponse({'status': 'error','message': 'Попытка подмены данных.Доступ запрещён!!!'},status=300)

            new_holder = data.get('holder','').strip()
            new_start_date = data.get('start_date','').strip()
            new_end_date = data.get('end_date','').strip()
            new_workload = data.get('workload','').strip()
            new_task_name = data.get('task_name','').strip()
            new_task_comment = data.get('task_comment','').strip()

            try:
                new_holder = User.objects.get(username=new_holder) if new_holder else None
            except User.DoesNotExist:
                return JsonResponse({'status': 'error','message': 'Такого пользователя не существует!!!'},status=600)
            
            try:
                new_start_date = datetime.strptime(new_start_date,date_template) if new_start_date else None
            except ValueError:
                return JsonResponse({'status': 'error','message': 'Неверная дата постановки задачи!!!'},status=100)

            try:
                new_end_date = datetime.strptime(new_end_date,date_template) if new_end_date else None
            except ValueError:
                return JsonResponse({'status': 'error','message': 'Неверная дата срока выполнения!!!'},status=100)
            
            try:
                new_workload = float(new_workload) if new_workload else 0.0
            except ValueError:
                return JsonResponse({'status': 'error','message': 'Неверное значение трудоёмкости!!!'},status=100)

            if not new_start_date or not new_task_name:
                return JsonResponse({'status': 'error','message': 'наименование и начальная дата задачи обязательны!!!'},status=200)

            new_task = Task.objects.create(
                project=project,
                holder=new_holder,
                start_date=new_start_date,
                end_date=new_end_date,
                workload=new_workload,
                task_name=new_task_name,
                task_comment=new_task_comment
            )

            return JsonResponse({
                'status': 'success',
                'message': 'Задача успешно добавлена!',
                'task_id': new_task.task_id
            })
        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            print("КРАШ НА БЭКЕНДЕ:", error_msg) 
            return JsonResponse({'status': 'error', 'message': error_msg}, status=200)

    return JsonResponse({'status': 'error','message': 'Неверный метод запроса!!!'},status=400)

@login_required
def delete_task(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            task_id = data.get('task_id')

            task = get_object_or_404(Task,task_id=task_id)

            is_kb_boss = request.user.groups.filter(name='Руководители КБ').exists()

            if not request.user.is_superuser and not is_kb_boss:
                return JsonResponse({
                        'status': 'error',
                        'message': 'Попытка подмены данных!Вы можете удалять только свои задачи'
                    },
                    status=300
                )
        
            task.delete()

            return JsonResponse({
                'status': 'success',
                'message': 'Задача успешно удалена!'
            })

        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            print("КРАШ НА БЭКЕНДЕ:", error_msg)
            return JsonResponse({'status': 'error', 'message': error_msg}, status=200)
 
    return JsonResponse({'status': 'error','message': 'Неверный метод запроса!!!'},status=400)

@login_required
def delete_project(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            project_id = data.get('project_id')

            project = get_object_or_404(Project,pr_id=project_id)

            is_kb_boss = request.user.groups.filter(name='Руководители КБ').exists()

            if not is_kb_boss and not request.user.is_superuser:
                return JsonResponse({
                        'status': 'error',
                        'message': 'Попытка подмены данных!Вы можете удалять только свои задачи'
                    },
                    status=300
                )
        
            project.delete()

            return JsonResponse({
                'status': 'success',
                'message': 'Проект успешно удалён!'
            })

        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            print("КРАШ НА БЭКЕНДЕ:", error_msg)
            return JsonResponse({'status': 'error', 'message': error_msg}, status=200)
 
    return JsonResponse({'status': 'error','message': 'Неверный метод запроса!!!'},status=400)

@login_required
def update_task(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            task_id = data.get('task_id')
            field_name = data.get('field')
            new_value = data.get('value')

            task = get_object_or_404(Task,task_id=task_id)

            is_kb_boss = request.user.groups.filter(name='Руководители КБ').exists()

            main_project = task.project.main_project

            if task.holder != request.user and not request.user.is_superuser and not is_kb_boss and request.user != main_project.gip:
                return JsonResponse({
                        'status': 'error',
                        'message': 'Попытка подмены данных!Вы можете модифицировать только свои задачи!'
                    },
                    status=300
                )
        
            if field_name== 'workload':
                try:
                    new_value = float(new_value) if new_value else 0.0
                except ValueError:
                    return JsonResponse({'status': 'error','message': 'Неверная трудоёмкость!!!'},status=100)
            else:
                if field_name == 'task_name' and not new_value:
                    return JsonResponse({'status': 'error','message': 'Наименование задачи не может быть пустым!!!'},status=100)
            
            setattr(task, field_name,new_value)
            task.save()
            return JsonResponse({
                'status': 'success',
                'message': 'Данные успешно сохранены!'
            })

        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            print("КРАШ НА БЭКЕНДЕ:", error_msg)
            return JsonResponse({'status': 'error', 'message': error_msg}, status=200)
 
    return JsonResponse({'status': 'error','message': 'Неверный метод запроса!!!'},status=400)

@login_required
def update_project(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            project_id = data.get('project_id')
            field_name = data.get('field')
            new_value = data.get('value')

            project = get_object_or_404(Project,pr_id=project_id)

            is_kb_boss = request.user.groups.filter(name='Руководители КБ').exists()

            if not request.user.is_superuser and not is_kb_boss:
                return JsonResponse({
                        'status': 'error',
                        'message': 'Попытка подмены данных!Вы не имеете прав на редактирование проекта!'
                    },
                    status=300
                )
        
            if field_name== 'volume':
                try:
                    new_value = float(new_value) if new_value else 0.0
                except ValueError:
                    return JsonResponse({'status': 'error','message': 'Неверный обьём!!!'},status=100)
            else:
                if field_name == 'status' and not new_value:
                    return JsonResponse({'status': 'error','message': 'Неверный статус!!!'},status=100)
            
            setattr(project, field_name,new_value)
            project.save()
            return JsonResponse({
                'status': 'success',
                'message': 'Данные успешно сохранены!'
            })

        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            print("КРАШ НА БЭКЕНДЕ:", error_msg)
            return JsonResponse({'status': 'error', 'message': error_msg}, status=200)
 
    return JsonResponse({'status': 'error','message': 'Неверный метод запроса!!!'},status=400)

def login_user(request):
    if request.user.is_authenticated:
        return redirect('global_kb_timeline')
    
    error = None

    if request.method == 'POST':
        username_input = request.POST.get('username','').strip()
        password_input = request.POST.get('password','')

        user = authenticate(request,username=username_input,password=password_input)

        if user is not None:
            if user.is_active:
                login(request,user)
                return redirect('global_kb_timeline')
            else:
                error = "Ваша учетная запись заблокирована!!!"
        
        else:
            error = "Неверное имя пользователя или пароль!"

    return render(request, 'core/login.html',{'error': error})

def logout_user(request):
    logout(request)
    return redirect('login_user')

def dashboard_view(request):
    return render(request,'core/dashboard.html')