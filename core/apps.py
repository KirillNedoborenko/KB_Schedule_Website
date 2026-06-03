from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    # ВОТ ЭТОТ МЕТОД ПОДКЛЮЧАЕТ НАШИ СИГНАЛЫ ПРИ СТАРТЕ СЕРВЕРА КБ:
    def ready(self):
        import core.signals # Django молча загрузит триггеры в память