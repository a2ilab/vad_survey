from django.apps import AppConfig

class VadSurveyConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'vad_survey'

    def ready(self):
        import vad_survey.signals  # 앱 이름으로 수정