from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('rifugi/<int:pk>/', views.rifugio, name='rifugio'),
    path('eventi/', views.eventi, name='eventi'),
    path('passaporto/', views.passaporto, name='passaporto'),
    path('gestore/', views.dashboard_gestore, name='dashboard_gestore'),
    path('admin-panel/', views.pannello_admin, name='pannello_admin'),
    path('rifugi/<int:pk>/prenota/', views.prenota, name='prenota'),
    path('guida/', views.dashboard_guida, name='dashboard_guida'),
    path('guide/', views.guide, name='guide'),
    path('itinerari/<int:pk>/iscriviti/', views.iscriviti_itinerario, name='iscriviti_itinerario'),
    path('checkin/', views.checkin, name='checkin'),
    path('rifugi/<int:pk>/preferito/', views.toggle_preferito, name='toggle_preferito'),
    path('rifugi/<int:pk>/recensione/', views.scrivi_recensione, name='scrivi_recensione'),
    path('profilo/modifica/', views.modifica_profilo, name='modifica_profilo'),
]