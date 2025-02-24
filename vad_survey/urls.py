from django.urls import path

from . import views

app_name = 'vad_survey'

urlpatterns = [
    path('', views.rate_words, name='rate_words'),
]