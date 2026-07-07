from django.contrib import admin
from .models import Rifugio, Visita, Timbro, Prenotazione, Recensione, Preferito, Evento, Itinerario, IscrizioneItinerario

@admin.register(Rifugio)
class RifugioAdmin(admin.ModelAdmin):
    list_display = ['nome', 'regione', 'altitudine', 'tipo', 'stato', 'gestore']
    list_filter = ['stato', 'tipo', 'regione']
    search_fields = ['nome', 'regione', 'localita']
    actions = ['approva_rifugi']

    def approva_rifugi(self, request, queryset):
        queryset.update(stato='approvato')
        self.message_user(request, f'{queryset.count()} rifugi approvati.')
    approva_rifugi.short_description = 'Approva rifugi selezionati'

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

@admin.register(Visita)
class VisitaAdmin(admin.ModelAdmin):
    list_display = ['escursionista', 'rifugio', 'data_visita']
    search_fields = ['escursionista__username', 'rifugio__nome']

@admin.register(Timbro)
class TimbroAdmin(admin.ModelAdmin):
    list_display = ['visita', 'data_assegnazione']

@admin.register(Preferito)
class PreferitoAdmin(admin.ModelAdmin):
    list_display = ['escursionista', 'rifugio']
    search_fields = ['escursionista__username', 'rifugio__nome']

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