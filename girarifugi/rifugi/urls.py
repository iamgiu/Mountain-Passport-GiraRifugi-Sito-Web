from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('rifugi/<int:pk>/', views.rifugio, name='rifugio'),
]