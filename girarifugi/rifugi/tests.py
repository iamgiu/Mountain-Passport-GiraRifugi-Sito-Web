from datetime import date, timedelta

from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from .models import Prenotazione, Rifugio, Visita


def crea_utente_in_gruppo(username, gruppo_nome):
    """Helper: crea un utente e lo aggiunge al gruppo indicato."""
    utente = User.objects.create_user(username=username, password="testpass123")
    gruppo, _ = Group.objects.get_or_create(name=gruppo_nome)
    utente.groups.add(gruppo)
    return utente


class PermessiViewTestCase(TestCase):
    """Verifica che il decorator gruppo_richiesto protegga correttamente le viste."""

    def setUp(self):
        self.escursionista = crea_utente_in_gruppo("escursionista_test", "Escursionista")
        self.gestore = crea_utente_in_gruppo("gestore_test", "GestoreRifugio")

    def test_escursionista_non_accede_dashboard_gestore(self):
        """Un escursionista che prova ad accedere alla dashboard del gestore
        deve ricevere un 403, non un redirect silenzioso o un 200."""
        self.client.login(username="escursionista_test", password="testpass123")
        response = self.client.get(reverse("dashboard_gestore"))
        self.assertEqual(response.status_code, 403)

    def test_gestore_accede_alla_propria_dashboard(self):
        """Un utente del gruppo corretto deve poter accedere regolarmente."""
        self.client.login(username="gestore_test", password="testpass123")
        response = self.client.get(reverse("dashboard_gestore"))
        self.assertEqual(response.status_code, 200)

    def test_utente_anonimo_viene_rediretto_al_login(self):
        """Un utente non autenticato non deve mai vedere una vista protetta,
        ma essere rediretto alla pagina di login."""
        response = self.client.get(reverse("dashboard_gestore"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)


class PrenotazioneValidazioneTestCase(TestCase):
    """Verifica il vincolo logico su Prenotazione: data_arrivo < data_partenza."""

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

    def test_data_arrivo_dopo_data_partenza_solleva_errore(self):
        prenotazione = Prenotazione(
            escursionista=self.escursionista,
            rifugio=self.rifugio,
            data_arrivo=date.today() + timedelta(days=5),
            data_partenza=date.today() + timedelta(days=2),
        )
        with self.assertRaises(ValidationError):
            prenotazione.full_clean()

    def test_date_valide_non_sollevano_errore(self):
        prenotazione = Prenotazione(
            escursionista=self.escursionista,
            rifugio=self.rifugio,
            data_arrivo=date.today() + timedelta(days=2),
            data_partenza=date.today() + timedelta(days=5),
        )
        # full_clean() valida anche i campi obbligatori: non deve sollevare eccezioni
        try:
            prenotazione.full_clean()
        except ValidationError as e:
            self.fail(f"full_clean() ha sollevato un errore inatteso: {e}")


class VisitaUnicitaTestCase(TestCase):
    """Verifica il vincolo unique_together su Visita: un escursionista
    non può registrare due volte la visita allo stesso rifugio."""

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

    def test_doppia_visita_stesso_rifugio_solleva_errore(self):
        Visita.objects.create(escursionista=self.escursionista, rifugio=self.rifugio)
        with self.assertRaises(Exception):
            # una seconda Visita identica viola unique_together a livello di DB
            Visita.objects.create(escursionista=self.escursionista, rifugio=self.rifugio)