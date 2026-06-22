from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('rifugi/<int:pk>/', views.rifugio, name='rifugio'),
    path('passaporto/', views.passaporto, name='passaporto'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('gestore/', views.dashboard_gestore, name='dashboard_gestore'),
    path('admin-panel/', views.pannello_admin, name='pannello_admin'),
    path('rifugi/<int:pk>/prenota/', views.prenota, name='prenota'),
]