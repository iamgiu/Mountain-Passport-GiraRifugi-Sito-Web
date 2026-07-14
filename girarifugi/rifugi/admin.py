from django.contrib import admin
from .models import Rifugio, Visita, Timbro, Prenotazione, Recensione, Preferito, Evento, Itinerario, IscrizioneItinerario

# GESTIONE DEI RIFUGI
# Configurazione dell'interfaccia di amministrazione per i rifugi
# Consente di visualizzare, filtrare e cercare i rifugi oltre che a fornire un'azione rapida per l'approvazione dei rifugi
# La funzione approva rifugi è una funzione che mi permette di approvare rapidamente i rifugi selezionati
@admin.register(Rifugio)
class RifugioAdmin(admin.ModelAdmin):
    list_display = ['nome', 'regione', 'altitudine', 'tipo', 'stato', 'gestore']    # Campi visualizzati nella lista dei rifugi
    list_filter = ['stato', 'tipo', 'regione']  # Filtri laterali
    search_fields = ['nome', 'regione', 'localita'] # Campi per la barra di ricerca 
    actions = ['approva_rifugi']    # Azione che mi permette di selezionare più righe contemporaneamente e approvare più rifugi contemporaneamente

    def approva_rifugi(self, request, queryset):
        queryset.update(stato='approvato')
        self.message_user(request, f'{queryset.count()} rifugi approvati.')
    approva_rifugi.short_description = 'Approva rifugi selezionati'

# GESTIONE PRENOTAZIONE E RECENSIONI
# Gestione delle prenotazioni effettuate dagli escursionisti presso i rifugi
# Moderazione e visualizzazione delle recensioni lasciate dali utenti
@admin.register(Prenotazione)
class PrenotazioneAdmin(admin.ModelAdmin):
    list_display = ['escursionista', 'rifugio', 'data_arrivo', 'data_partenza', 'num_ospiti', 'stato']
    list_filter = ['stato']
    search_fields = ['escursionista__username', 'rifugio__nome']

@admin.register(Recensione)
class RecensioneAdmin(admin.ModelAdmin):
    list_display = ['escursionista', 'rifugio', 'voto', 'data']
    list_filter = ['voto']
    search_fields = ['escursionista__username', 'rifugio__nome']

# GESTIONE VISITE E TIMBRI 
# Conteggio delle visite effetive degli escursionista ai rifugi
# Gestione dei timbri digitali associati alle vistie
@admin.register(Visita)
class VisitaAdmin(admin.ModelAdmin):
    list_display = ['escursionista', 'rifugio', 'data_visita']
    search_fields = ['escursionista__username', 'rifugio__nome']

@admin.register(Timbro)
class TimbroAdmin(admin.ModelAdmin):
    list_display = ['escursionista', 'rifugio', 'data_assegnazione']

# PREFERITI 
# Gestisce la sezione dei Preferiti che gli utenti usano quindi è una sorta di tabella di relazione (molti a molti) che collega un escursionista a un rifugio che ha deciso di salvare
@admin.register(Preferito)
class PreferitoAdmin(admin.ModelAdmin):
    list_display = ['escursionista', 'rifugio']
    search_fields = ['escursionista__username', 'rifugio__nome']

# EVENTI E ITINERARI
# Pianificazione degli eventi organizzati direttamente dai rifugi
# Pianificazione degli itinerari organizzati direttamente dalle guide con anche gestione delle iscrizioni
@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    list_display = ['titolo', 'rifugio', 'data', 'ora', 'posti_disponibili']
    list_filter = ['data']
    search_fields = ['titolo', 'rifugio__nome']

@admin.register(Itinerario)
class ItinerarioAdmin(admin.ModelAdmin):
    list_display = ['titolo', 'guida', 'data', 'difficolta', 'posti_disponibili']
    list_filter = ['difficolta']
    search_fields = ['titolo', 'guida__username']

@admin.register(IscrizioneItinerario)
class IscrizioneItinerarioAdmin(admin.ModelAdmin):
    list_display = ['escursionista', 'itinerario', 'data_iscrizione']
    search_fields = ['escursionista__username', 'itinerario__titolo']