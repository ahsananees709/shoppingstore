from django.urls import path
from playground import  views

urlpatterns = [
    path('home/', views.start_app),
]
