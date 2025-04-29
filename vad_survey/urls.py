from django.urls import path

from . import views

app_name = 'vad_survey'
# url 추가
urlpatterns = [
    path('intro/', views.intro, name='intro'),
    path('rate/', views.rate_words, name='rate_words'),
]