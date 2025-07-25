from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('quiz/<int:quiz_id>/', views.quiz_detail, name='quiz_detail'),
    path('quiz/<int:quiz_id>/submit/', views.submit_answers, name='submit_answers'),
    path('get_recommendation/', views.get_recommendation, name='get_recommendation'), 

]