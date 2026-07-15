from datetime import date, timedelta
from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from .models import Prenotazione, Rifugio, Visita

# Crea un utente di test nel database
def crea_utente_in_gruppo(username, gruppo_nome):
    """Helper: crea un utente e lo aggiunge al gruppo indicato."""
    utente = User.objects.create_user(username=username, password="testpass123")
    gruppo, _ = Group.objects.get_or_create(name=gruppo_nome)
    utente.groups.add(gruppo)
    return utente

# Verifica che la logica dei permessi protegga correttamente l'accesso alle aree riservate
class PermessiViewTestCase(TestCase):

    def setUp(self):
        self.escursionista = crea_utente_in_gruppo("escursionista_test", "Escursionista")
        self.gestore = crea_utente_in_gruppo("gestore_test", "GestoreRifugio")

    # Verifica che un escusionista non possa accedere alla dashboard del gestore
    def test_escursionista_non_accede_dashboard_gestore(self):
        self.client.login(username="escursionista_test", password="testpass123")
        response = self.client.get(reverse("dashboard_gestore"))
        self.assertEqual(response.status_code, 403)

    # Verifica che un gestore possa accedere alla propria dashboard
    def test_gestore_accede_alla_propria_dashboard(self):
        self.client.login(username="gestore_test", password="testpass123")
        response = self.client.get(reverse("dashboard_gestore"))
        self.assertEqual(response.status_code, 200)

    # Verifica che un utente non autenticato venta reindirizzato verso la pagina di login quando tenta di accedere alla dashboard del gestore
    def test_utente_anonimo_viene_rediretto_al_login(self):
        response = self.client.get(reverse("dashboard_gestore"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

# Verifica che i vincoli sulle date di prenotazione definiti vengano applicati correttamente
class PrenotazioneValidazioneTestCase(TestCase):
    # Crea un escursionista e un test per poter simulare una prenotazione
    def setUp(self):
        self.escursionista = crea_utente_in_gruppo("escursionista_test", "Escursionista")
        self.rifugio = Rifugio.objects.create(
            nome="Rifugio Test",
            localita="Val Test",
            altitudine=2000,
            latitudine=45.0,
            longitudine=7.0,
            regione="Piemonte",
            stato="approvato",
        )

    # Crea una prenotazione non valida ovvero l'arrivo è dopo la partenza
    def test_data_arrivo_dopo_data_partenza_solleva_errore(self):
        prenotazione = Prenotazione(
            escursionista=self.escursionista,
            rifugio=self.rifugio,
            data_arrivo=date.today() + timedelta(days=5),   # Arrivo tra 5 giorni
            data_partenza=date.today() + timedelta(days=2), # Attivo tra 2 giorni
        )
        with self.assertRaises(ValidationError):
            prenotazione.full_clean()

    # Crea una prenotazione valida ovvero l'arrivo è prima della partenza
    def test_date_valide_non_sollevano_errore(self):
        prenotazione = Prenotazione(
            escursionista=self.escursionista,
            rifugio=self.rifugio,
            data_arrivo=date.today() + timedelta(days=2),   # Arrivo tra 2 giorni
            data_partenza=date.today() + timedelta(days=5), # Arrivo tra 5 giorni
        )
        try:
            prenotazione.full_clean()
        except ValidationError as e:
            self.fail(f"full_clean() ha sollevato un errore inatteso: {e}")