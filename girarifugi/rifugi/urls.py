from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),  # Pagina principale home
    path('register/', views.register, name='register'), # Registrazione di un nuovo utente

    # Rifugi: Dettagio, Preferiti, Recensioni e Prenotazioni
    path('rifugi/<int:pk>/', views.rifugio, name='rifugio'),
    path('rifugi/<int:pk>/prenota/', views.prenota, name='prenota'),
    path('rifugi/<int:pk>/preferito/', views.toggle_preferito, name='toggle_preferito'),
    path('rifugi/<int:pk>/recensione/', views.scrivi_recensione, name='scrivi_recensione'),

    # Eventi e Itinerari
    path('eventi/', views.eventi, name='eventi'),
    path('eventi/<int:pk>/iscriviti/', views.iscriviti_evento, name='iscriviti_evento'),
    path('itinerari/<int:pk>/iscriviti/', views.iscriviti_itinerario, name='iscriviti_itinerario'),

    # Aree Escusionista
    path('checkin/', views.checkin, name='checkin'),
    path('profilo/modifica/', views.modifica_profilo, name='modifica_profilo'),
    path('passaporto/', views.passaporto, name='passaporto'),

    # Dashboard e gestione Gestore, Guida e Admin
    path('gestore/', views.dashboard_gestore, name='dashboard_gestore'),
    path('admin-panel/', views.pannello_admin, name='pannello_admin'),
    path('guida/', views.dashboard_guida, name='dashboard_guida'),
    path('guide/', views.guide, name='guide'),

    # API
    path('check-username/', views.check_username, name='check_username'),   # Controllare in tempo reale se un username è già preso durante la registrazione
]