from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import date
import uuid

class Rifugio(models.Model):

    nome = models.CharField(max_length=200)
    localita = models.CharField(max_length=200)
    altitudine = models.IntegerField()
    latitudine = models.FloatField()
    longitudine = models.FloatField()
    regione = models.CharField(max_length=100)
    mensile = models.BooleanField(default=False)

    TIPO_CHOICES = [
        ('RIFUGIO', 'Rifugio'),
        ('BIVACCO', 'Bivacco'),
        ('CAPANNA', 'Capanna'),
    ]
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='RIFUGIO')

    descrizione = models.TextField(blank=True)
    posti_letto = models.IntegerField(default=0)
    posti_disponibili = models.IntegerField(default=0)
    immagine = models.ImageField(upload_to='rifugi/', blank=True, null=True)
    qr_uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    STATO_CHOICES = [
        ('in_attesa', 'In attesa'),
        ('approvato', 'Approvato'),
    ]
    stato = models.CharField(max_length=20, choices=STATO_CHOICES, default='in_attesa')

    gestore = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rifugi'
    )

    class Meta:
        verbose_name_plural = "Rifugi"

    def __str__(self):
        return f"{self.nome} ({self.regione})"
    
class Visita(models.Model):

    escursionista = models.ForeignKey (
        User,
        on_delete=models.CASCADE,
        related_name='visite'
    )

    rifugio = models.ForeignKey (
        Rifugio,
        on_delete=models.CASCADE,
        related_name='visite'
    )

    data_visita = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Visite"
        unique_together = ('escursionista', 'rifugio')


    def __str__(self):
        return f"{self.escursionista.username} ({self.rifugio.nome})"
    
class Timbro(models.Model):

    visita = models.OneToOneField(
        Visita,
        on_delete=models.CASCADE,
        related_name='timbro'
    )

    data_assegnazione = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Timbri"

    def __str__(self):
        return f"Timbro: {self.visita.rifugio.nome} - {self.visita.escursionista.username}"
    

class Prenotazione(models.Model):

    escursionista = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='prenotazioni'
    )

    rifugio = models.ForeignKey(
        Rifugio,
        on_delete=models.CASCADE,
        related_name='prenotazioni'
    )

    data_arrivo = models.DateField()
    data_partenza = models.DateField()
    num_ospiti = models.IntegerField(default=1)
    
    STATO_CHOICES = [
        ('in_attesa', 'In attesa'),
        ('approvata', 'Approvata'),
        ('rifiutata', 'Rifiutata'),
    ]
    stato = models.CharField(max_length=20, choices=STATO_CHOICES, default='in_attesa')

    posti_restituiti = models.BooleanField(default=False)

    def clean(self):
        if self.data_arrivo and self.data_arrivo < date.today():
            raise ValidationError("Non puoi prenotare una data già passata.")
        if self.data_arrivo and self.data_partenza:
            if self.data_arrivo >= self.data_partenza:
                raise ValidationError("La data di arrivo deve essere prima della data di partenza.")
    
    class Meta:
        verbose_name_plural = "Prenotazioni"

    def __str__(self):
        return f"{self.escursionista.username} - {self.rifugio.nome} ({self.stato}) "
    
class Itinerario(models.Model):
        
    guida = models.ForeignKey(
            User,
            on_delete=models.CASCADE,
            related_name='itinerari'
        )
    
    titolo = models.CharField(max_length=200)
    descrizione = models.TextField(blank=True)
    rifugi = models.ManyToManyField(Rifugio, related_name='itinerari', blank=True)
    data = models.DateField()
    ora = models.TimeField(blank=True, null=True)
    difficolta = models.CharField(max_length=20, choices=[
        ('facile', 'Facile'),
        ('medio', 'Medio'),
        ('difficile', 'Difficile'),
        ('esperto', 'Esperto'),
    ], default='facile')
    posti_disponibili = models.IntegerField(default=0)

    class Meta:
        verbose_name_plural = "Itinerari"
        ordering = ['data']

    def __str__(self):
        return f"{self.titolo} — {self.guida.username} ({self.data})"

class IscrizioneItinerario(models.Model):
    escursionista = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='iscrizioni_itinerari'
    )
    itinerario = models.ForeignKey(
        Itinerario,
        on_delete=models.CASCADE,
        related_name='iscrizioni'
    )
    data_iscrizione = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Iscrizioni Itinerari"
        unique_together = ('escursionista', 'itinerario')

    def __str__(self):
        return f"{self.escursionista.username} — {self.itinerario.titolo}"
    
class ProfiloGuida(models.Model):
    guida = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profilo_guida'
    )
    bio = models.TextField(blank=True)
    foto = models.ImageField(upload_to='guide/', blank=True, null=True)

    def __str__(self):
        return f"Profilo di {self.guida.username}"

class Recensione(models.Model):

    escursionista = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recensioni'
    )

    rifugio = models.ForeignKey(
        Rifugio,
        on_delete=models.CASCADE,
        related_name='recensioni'
    )

    testo = models.TextField()

    voto = models.IntegerField(

        validators=[MinValueValidator(1), MaxValueValidator(5)]

    )

    data = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Recensioni"

    def __str__(self):
        return f"{self.escursionista.username} - {self.rifugio.nome} ({self.voto}/5)"

class Preferito(models.Model):

    escursionista = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='preferiti'
    )

    rifugio = models.ForeignKey(
        Rifugio,
        on_delete=models.CASCADE,
        related_name='preferiti'
    )
    
class Evento(models.Model):
    rifugio = models.ForeignKey(
        Rifugio,
        on_delete=models.CASCADE,
        related_name='eventi'
    )
    titolo = models.CharField(max_length=200)
    descrizione = models.TextField(blank=True)
    data = models.DateField()
    ora = models.TimeField(blank=True, null=True)
    posti_disponibili = models.IntegerField(default=0)
    immagine = models.ImageField(upload_to='eventi/', blank=True, null=True)

    class Meta:
        verbose_name_plural = "Eventi"
        ordering = ['data']

    def __str__(self):
        return f"{self.titolo} — {self.rifugio.nome} ({self.data})"
        
class IscrizioneEvento(models.Model):
    escursionista = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='iscrizioni_eventi'
    )
    evento = models.ForeignKey(
        Evento,
        on_delete=models.CASCADE,
        related_name='iscrizioni'
    )
    data_iscrizione = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Iscrizioni Eventi"
        unique_together = ('escursionista', 'evento')

    def __str__(self):
        return f"{self.escursionista.username} — {self.evento.titolo}"