from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from .models import MainProject,Task
from datetime import datetime,timedelta

@login_required
def main_project_detail(request, mp_id):
    main_project = get_object_or_404(MainProject, mp_id=mp_id)

    if not request.user.is_superuser and request.user not in main_project.allowed_users.all():
        raise PermissionDenied("У вас нет прав доступа к этому КИПУ")
    
    sub_projects = main_project.projects.all()

    tasks = Task.objects.filter(project__main__project=main_project).select_related('holder','project')

    return render(request, 'core/project_detail.html', {
        'main_project': main_project,
        'sub_projects': sub_projects,
        'tasks': tasks
    })

@login_required
def global_kb_Schedule(request):
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

