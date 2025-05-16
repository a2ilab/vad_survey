from django.urls import path

from . import views

app_name = 'vad_survey'
# url 추가
urlpatterns = [
    path('intro/', views.intro, name='intro'),
    path('intro2/', views.intro2, name='intro2'),
    path('practice/', views.practice, name='practice'),
    path('rate/', views.rate_words, name='rate_words'),
]