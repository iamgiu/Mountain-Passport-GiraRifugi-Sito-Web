from django.db import models
from django.contrib.auth.models import User
import uuid

class Rifugio(models.Model):

    nome = models.CharField(max_length=200)
    localita = models.CharField(max_length=200)
    altitudine = models.IntegerField()
    latitudine = models.FloatField()
    longitudine = models.FloatField()
    regione = models.CharField(max_length=100)

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
        unique_together = ('escursionista', 'rifugio')


    def __str__(self):
        return f"{self.escursionista.username} ({self.rifugio.nome})"