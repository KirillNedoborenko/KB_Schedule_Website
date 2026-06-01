from .models import MainProject

def allowed_tabs_processor(request):
    if request.user.is_authenticated:
        if request.user.is_superuser or request.user.has_perm('core.view_all_main_projects'):
            return {'available_tabs': MainProject.objects.all().order_by('mp_name')}
        return {'available_tabs': request.user.allowed_main_projects.all().order_by('mp_name')}
    return {'available_tabs': []}