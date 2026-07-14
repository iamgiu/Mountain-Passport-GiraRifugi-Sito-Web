from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import redirect_to_login
from django.contrib.auth.models import Group, User
from django.contrib.auth.models import User as AuthUser
from django.db.models import Q
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from datetime import date, timedelta
from django.utils import timezone
from django.http import JsonResponse
from django import forms
from django.contrib.auth import update_session_auth_hash
from .models import Rifugio, Visita, Timbro, Prenotazione, Recensione, Preferito, Evento, Itinerario, IscrizioneItinerario, IscrizioneEvento, ProfiloGuida

# ─── MIXIN PERMESSI ───────────────────────────────────────────────────────────

def gruppo_richiesto(nome_gruppo):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            if not request.user.groups.filter(name=nome_gruppo).exists() and not request.user.is_superuser:
                return render(request, '403.html', status=403)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

# ─── UTILITY PRENOTAZIONI ─────────────────────────────────────────────────────

def punti_rifugio(rifugio):
    """I rifugi mensili valgono doppi punti."""
    return rifugio.altitudine * 2 if rifugio.mensile else rifugio.altitudine

def aggiorna_posti_disponibili(rifugio):
    """
    Restituisce al rifugio i posti occupati dalle prenotazioni approvate
    il cui soggiorno è ormai passato, una sola volta per prenotazione
    (grazie al flag posti_restituiti).
    """
    from django.db.models import Sum

    prenotazioni_scadute = Prenotazione.objects.filter(
        rifugio=rifugio,
        stato='approvata',
        data_partenza__lte=date.today(),
        posti_restituiti=False
    )

    totale = prenotazioni_scadute.aggregate(tot=Sum('num_ospiti'))['tot'] or 0

    if totale:
        rifugio.posti_disponibili = min(rifugio.posti_letto, rifugio.posti_disponibili + totale)
        rifugio.save()
        prenotazioni_scadute.update(posti_restituiti=True)

# ─── FORM REGISTRAZIONE ───────────────────────────────────────────────────────

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        fields = ['username', 'email', 'password1', 'password2']

# ─── FORM GESTORE ───────────────────────────────────────────────────────

class ModificaRifugioForm(forms.ModelForm):
    class Meta:
        model = Rifugio
        fields = ['descrizione', 'posti_disponibili']

class NuovoRifugioForm(forms.ModelForm):
    class Meta:
        model = Rifugio
        fields = ['nome', 'localita', 'altitudine', 'latitudine', 'longitudine', 'regione', 'tipo', 'descrizione', 'posti_letto', 'posti_disponibili', 'immagine']

class EventoForm(forms.ModelForm):
    class Meta:
        model = Evento
        fields = ['rifugio', 'titolo', 'descrizione', 'data', 'ora', 'posti_disponibili', 'immagine']

class ItinerarioForm(forms.ModelForm):
    class Meta:
        model = Itinerario
        fields = ['titolo', 'descrizione', 'data', 'ora', 'difficolta', 'posti_disponibili']

# ─── VISTE PUBBLICHE ──────────────────────────────────────────────────────────

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            gruppo = Group.objects.get(name='Escursionista')
            user.groups.add(gruppo)
            return redirect('/accounts/login/')
    else:
        form = RegisterForm()
    return render(request, 'registration/register.html', {'form': form})

def home(request):

    # Variabili comuni sempre calcolate
    rifugi_mensili = Rifugio.objects.filter(stato='approvato', mensile=True)
    rifugi_casuali = Rifugio.objects.filter(stato='approvato').order_by('?')[:10]
    rifugi_in_attesa_count = Rifugio.objects.filter(stato='in_attesa').count()

    # Variabili per ruolo
    rifugi_preferiti = []
    rifugi_paginati = None
    rifugi_gestore = []
    prenotazioni_in_attesa = 0
    itinerari_guida = []
    classifica_rapida = []
    guide = []
    gestori = []
    nome = regione = quota_min = quota_max = ''

    # Reset esplicito dei filtri (dal bottone "Reimposta filtri")
    if request.GET.get('reset') == '1':
        request.session.pop('filtri', None)
        return redirect('home')

    if request.user.is_authenticated:
        gruppo = request.user.groups.first()
        nome_gruppo = gruppo.name if gruppo else ''

        if nome_gruppo == 'Escursionista':
            preferiti = Preferito.objects.filter(escursionista=request.user).select_related('rifugio')
            rifugi_preferiti = [p.rifugio for p in preferiti]
            rifugi = Rifugio.objects.filter(stato='approvato')

            # Se non sono stati passati parametri di ricerca in GET, ripristina
            # gli ultimi filtri usati salvati in sessione.
            filtri_sessione = request.session.get('filtri', {})
            has_query_params = any(k in request.GET for k in ('nome', 'regione', 'quota_min', 'quota_max'))
            if has_query_params:
                nome = request.GET.get('nome', '')
                regione = request.GET.get('regione', '')
                quota_min = request.GET.get('quota_min', '')
                quota_max = request.GET.get('quota_max', '')
            else:
                nome = filtri_sessione.get('nome', '')
                regione = filtri_sessione.get('regione', '')
                quota_min = filtri_sessione.get('quota_min', '')
                quota_max = filtri_sessione.get('quota_max', '')

            visite = Visita.objects.filter(escursionista=request.user).select_related('rifugio')
            if nome: rifugi = rifugi.filter(nome__icontains=nome)
            if regione: rifugi = rifugi.filter(regione__icontains=regione)
            if quota_min: rifugi = rifugi.filter(altitudine__gte=quota_min)
            if quota_max: rifugi = rifugi.filter(altitudine__lte=quota_max)
            request.session['filtri'] = {
                'nome': nome, 'regione': regione,
                'quota_min': quota_min, 'quota_max': quota_max
            }
            paginator = Paginator(rifugi, 10)
            rifugi_paginati = paginator.get_page(request.GET.get('page'))

        elif nome_gruppo == 'GestoreRifugio':
            rifugi_gestore = Rifugio.objects.filter(gestore=request.user)
            prenotazioni_in_attesa = Prenotazione.objects.filter(
                rifugio__gestore=request.user, stato='in_attesa'
            ).count()

        elif nome_gruppo == 'GuidaAlpina':
            preferiti = Preferito.objects.filter(escursionista=request.user).select_related('rifugio')
            rifugi_preferiti = [p.rifugio for p in preferiti]
            itinerari_guida = Itinerario.objects.filter(guida=request.user, data__gte=date.today()).order_by('data')

        elif nome_gruppo == 'Admin' or request.user.is_superuser:
            now = timezone.now()
            escursionisti = AuthUser.objects.filter(groups__name='Escursionista')
            for u in escursionisti:
                visite = Visita.objects.filter(
                    escursionista=u,
                    data_visita__year=now.year,
                    data_visita__month=now.month
                ).select_related('rifugio')
                punti = sum(punti_rifugio(v.rifugio) for v in visite)
                classifica_rapida.append({
                    'username': u.username,
                    'email': u.email,
                    'punti': punti,
                    'num_visite': visite.count()
                })
            classifica_rapida.sort(key=lambda x: x['punti'], reverse=True)
            classifica_rapida = classifica_rapida[:5]

            guide = AuthUser.objects.filter(groups__name='GuidaAlpina').prefetch_related('itinerari')
            gestori = AuthUser.objects.filter(groups__name='GestoreRifugio').prefetch_related('rifugi')

            # Crea nuovo utente
            if request.method == 'POST' and request.POST.get('azione') == 'crea_utente':
                username = request.POST.get('username')
                password = request.POST.get('password')
                email = request.POST.get('email', '')
                ruolo = request.POST.get('ruolo')
                if username and password and ruolo:
                    if not AuthUser.objects.filter(username=username).exists():
                        nuovo = AuthUser.objects.create_user(username=username, password=password, email=email)
                        gruppo_obj = Group.objects.get(name=ruolo)
                        nuovo.groups.add(gruppo_obj)
                        messages.success(request, f'Utente {username} creato come {ruolo}!')
                    else:
                        messages.error(request, 'Username già esistente.')
                return redirect('home')

    return render(request, 'home.html', {
        'rifugi': rifugi_paginati,
        'rifugi_preferiti': rifugi_preferiti,
        'rifugi_mensili': rifugi_mensili,
        'rifugi_casuali': rifugi_casuali,
        'rifugi_gestore': rifugi_gestore,
        'prenotazioni_in_attesa': prenotazioni_in_attesa,
        'itinerari_guida': itinerari_guida,
        'rifugi_in_attesa_count': rifugi_in_attesa_count,
        'classifica_rapida': classifica_rapida,
        'guide': guide,
        'gestori': gestori,
        'nome': nome, 'regione': regione,
        'quota_min': quota_min, 'quota_max': quota_max,
    })

def visite_mese_corrente(queryset_visite):
    """Filtra un queryset di Visita al solo mese corrente."""
    now = timezone.now()
    return queryset_visite.filter(data_visita__year=now.year, data_visita__month=now.month)

def rifugio(request, pk):
    r = get_object_or_404(Rifugio, pk=pk)
    aggiorna_posti_disponibili(r)
    recensioni = Recensione.objects.filter(rifugio=r).select_related('escursionista').order_by('-data')

    prenotazione = None
    ha_timbro = False
    recensione_utente = None
    e_preferito = False
    soggiorno_in_corso = False  # ← nuovo

    if request.user.is_authenticated:
        prenotazione = Prenotazione.objects.filter(
            escursionista=request.user, rifugio=r
        ).first()
        ha_timbro = Visita.objects.filter(
            escursionista=request.user, rifugio=r
        ).exists()
        recensione_utente = Recensione.objects.filter(
            escursionista=request.user, rifugio=r
        ).first()
        e_preferito = Preferito.objects.filter(
            escursionista=request.user, rifugio=r
        ).exists()

    # Il soggiorno è "in corso" se oggi è tra arrivo e partenza (inclusi)
    if prenotazione and prenotazione.stato == 'approvata':
        if prenotazione.data_arrivo < date.today() <= prenotazione.data_partenza:
            soggiorno_in_corso = True  # ← nuovo

    if prenotazione and prenotazione.data_partenza < date.today():
        prenotazione = None

    return render(request, 'rifugi/rifugio.html', {
        'rifugio': r,
        'recensioni': recensioni,
        'prenotazione': prenotazione,
        'ha_timbro': ha_timbro,
        'recensione_utente': recensione_utente,
        'e_preferito': e_preferito,
        'soggiorno_in_corso': soggiorno_in_corso,  # ← nuovo
    })

def guide(request):
    is_admin = request.user.is_authenticated and (
        request.user.groups.filter(name='Admin').exists() or request.user.is_superuser
    )

    if request.method == 'POST' and is_admin:
        azione = request.POST.get('azione')

        if azione == 'modifica_profilo_guida_admin':
            pk = request.POST.get('guida_pk')
            guida_target = get_object_or_404(AuthUser, pk=pk, groups__name='GuidaAlpina')
            profilo, creato = ProfiloGuida.objects.get_or_create(guida=guida_target)
            profilo.bio = request.POST.get('bio', '')
            if request.FILES.get('foto'):
                profilo.foto = request.FILES['foto']
            profilo.save()
            guida_target.first_name = request.POST.get('first_name', '')
            guida_target.save()
            messages.success(request, 'Guida aggiornata!')
            return redirect('guide')

    # Tutte le guide, con il loro profilo (se esiste), filtrabili per nome
    guide_lista = AuthUser.objects.filter(groups__name='GuidaAlpina').select_related('profilo_guida').order_by('username')
    guida_q = request.GET.get('guida_q', '')
    if guida_q:
        guide_lista = guide_lista.filter(
            Q(username__icontains=guida_q) | Q(first_name__icontains=guida_q) | Q(last_name__icontains=guida_q)
        )

    # Itinerari futuri, filtrabili
    itinerari = Itinerario.objects.select_related('guida').prefetch_related('iscrizioni').filter(data__gte=date.today())
    q = request.GET.get('q', '')
    difficolta = request.GET.get('difficolta', '')
    if q:
        itinerari = itinerari.filter(titolo__icontains=q)
    if difficolta:
        itinerari = itinerari.filter(difficolta=difficolta)

    iscrizioni_utente = []
    if request.user.is_authenticated:
        iscrizioni_utente = list(
            IscrizioneItinerario.objects.filter(escursionista=request.user).values_list('itinerario_id', flat=True)
        )

    return render(request, 'guide.html', {
        'guide_lista': guide_lista,
        'guida_q': guida_q,
        'itinerari': itinerari,
        'iscrizioni_utente': iscrizioni_utente,
        'q': q,
        'difficolta': difficolta,
        'is_admin': is_admin,
    })

@gruppo_richiesto('Escursionista')
def iscriviti_itinerario(request, pk):
    it = get_object_or_404(Itinerario, pk=pk)
    if request.method == 'POST':
        if it.posti_disponibili > 0:
            _, created = IscrizioneItinerario.objects.get_or_create(
                escursionista=request.user,
                itinerario=it
            )
            if created:
                it.posti_disponibili -= 1
                it.save()
                messages.success(request, f'Iscritto a {it.titolo}!')
            else:
                messages.warning(request, 'Sei già iscritto a questo itinerario.')
        else:
            messages.error(request, 'Posti esauriti.')
    return redirect('guide')

@gruppo_richiesto('Escursionista')
def iscriviti_evento(request, pk):
    evento = get_object_or_404(Evento, pk=pk)
    if request.method == 'POST':
        if evento.posti_disponibili > 0:
            _, created = IscrizioneEvento.objects.get_or_create(
                escursionista=request.user,
                evento=evento
            )
            if created:
                evento.posti_disponibili -= 1
                evento.save()
                messages.success(request, f'Iscritto a {evento.titolo}!')
            else:
                messages.warning(request, 'Sei già iscritto.')
        else:
            messages.error(request, 'Posti esauriti.')
    return redirect('eventi')

def eventi(request):
    qs = Evento.objects.select_related('rifugio').filter(data__gte=date.today())
    q = request.GET.get('q', '')
    regione = request.GET.get('regione', '')
    dal = request.GET.get('dal', '')
    if q:
        qs = qs.filter(titolo__icontains=q)
    if regione:
        qs = qs.filter(rifugio__regione__icontains=regione)
    if dal:
        qs = qs.filter(data__gte=dal)

    iscrizioni_utente = []
    if request.user.is_authenticated:
        iscrizioni_utente = list(
            IscrizioneEvento.objects.filter(escursionista=request.user).values_list('evento_id', flat=True)
        )

    return render(request, 'eventi.html', {
        'eventi': qs,
        'iscrizioni_utente': iscrizioni_utente,
        'q': q, 'regione': regione, 'dal': dal,
    })

def check_username(request):
    username = request.GET.get('username', '').strip()
    esiste = False
    if username:
        esiste = AuthUser.objects.filter(username__iexact=username).exists()
    return JsonResponse({'esiste': esiste})

# ─── VISTE RISTRETTE ──────────────────────────────────────────────────────────

@gruppo_richiesto('Escursionista')
def passaporto(request):
    visite = Visita.objects.filter(escursionista=request.user).select_related('rifugio', 'timbro').order_by('-data_visita')
    recensioni = Recensione.objects.filter(escursionista=request.user).select_related('rifugio').order_by('-data')
    prenotazioni = Prenotazione.objects.filter(escursionista=request.user)
    preferiti_qs = Preferito.objects.filter(escursionista=request.user)

    now = timezone.now()
    visite_mese = visite.filter(data_visita__year=now.year, data_visita__month=now.month)
    punti_totali = sum(punti_rifugio(v.rifugio) for v in visite_mese)

    attivita = []
    trenta_giorni_fa = timezone.now() - timedelta(days=30)

    for v in visite.filter(data_visita__gte=trenta_giorni_fa)[:5]:
        attivita.append({'icona': 'landscape', 'testo': f'Hai visitato {v.rifugio.nome}', 'data': v.data_visita})

    for p in prenotazioni.filter(data_arrivo__gte=trenta_giorni_fa.date()).order_by('-id')[:3]:
        attivita.append({'icona': 'calendar_today', 'testo': f'Hai prenotato {p.rifugio.nome}', 'data': p.data_arrivo})

    for f in preferiti_qs.order_by('-id')[:3]:
        attivita.append({'icona': 'bookmark', 'testo': f'Hai salvato {f.rifugio.nome} nei preferiti', 'data': date.today()})

    return render(request, 'rifugi/passaporto.html', {
        'visite': visite,
        'recensioni': recensioni,
        'attivita': attivita,
        'punti_totali': punti_totali,
        'num_visite': visite.count(),
        'num_prenotazioni': prenotazioni.count(),
        'num_preferiti': preferiti_qs.count(),
    })

@gruppo_richiesto('Escursionista')
def toggle_preferito(request, pk):
    rifugio = get_object_or_404(Rifugio, pk=pk)
    if request.method == 'POST':
        preferito, created = Preferito.objects.get_or_create(
            escursionista=request.user,
            rifugio=rifugio
        )
        if not created:
            preferito.delete()
            aggiunto = False
        else:
            aggiunto = True

        # Se la richiesta arriva da JavaScript (Fetch), rispondi in JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'aggiunto': aggiunto})

        # Fallback senza JS: comportamento originale con redirect
        if aggiunto:
            messages.success(request, f'{rifugio.nome} aggiunto ai preferiti!')
        else:
            messages.info(request, f'{rifugio.nome} rimosso dai preferiti.')
    return redirect('rifugio', pk=pk)

@gruppo_richiesto('Escursionista')
def prenota(request, pk):
    rifugio = get_object_or_404(Rifugio, pk=pk)
    if request.method == 'POST':
        data_arrivo = request.POST.get('data_arrivo')
        data_partenza = request.POST.get('data_partenza')
        num_ospiti = int(request.POST.get('num_ospiti', 1))

        # Elimina prenotazione rifiutata precedente
        Prenotazione.objects.filter(
            escursionista=request.user,
            rifugio=rifugio,
            stato='rifiutata'
        ).delete()

        prenotazione = Prenotazione(
            escursionista=request.user,
            rifugio=rifugio,
            data_arrivo=data_arrivo,
            data_partenza=data_partenza,
            num_ospiti=num_ospiti,
        )
        try:
            prenotazione.full_clean()
            prenotazione.save()
            messages.success(request, 'Prenotazione inviata! Attendi l\'approvazione del gestore.')
        except Exception as e:
            messages.error(request, f'Errore: {e}')
    return redirect('rifugio', pk=pk)

@gruppo_richiesto('Escursionista')
def checkin(request):
    if request.method == 'POST':
        codice = request.POST.get('codice', '').strip().lower()
        try:
            # Cerca il rifugio il cui UUID inizia con il codice inserito
            rifugi = Rifugio.objects.filter(stato='approvato')
            rifugio = None
            for r in rifugi:
                if str(r.qr_uuid).replace('-', '')[:8].upper() == codice.upper():
                    rifugio = r
                    break

            if not rifugio:
                messages.error(request, 'Codice non valido.')
                return redirect('checkin')

            visita, created = Visita.objects.get_or_create(
                escursionista=request.user,
                rifugio=rifugio
            )
            if created:
                Timbro.objects.create(visita=visita)
                messages.success(request, f'Check-in effettuato al {rifugio.nome}! +{punti_rifugio(rifugio)} punti!')
            else:
                messages.info(request, f'Hai già il timbro per {rifugio.nome}!')

        except Exception as e:
            messages.error(request, f'Errore: {e}')

        return redirect('passaporto')

    return render(request, 'checkin.html')

@gruppo_richiesto('Escursionista')
def scrivi_recensione(request, pk):
    rifugio = get_object_or_404(Rifugio, pk=pk)
    ha_timbro = Visita.objects.filter(escursionista=request.user, rifugio=rifugio).exists()

    if not ha_timbro:
        messages.error(request, 'Devi aver visitato il rifugio per scrivere una recensione.')
        return redirect('rifugio', pk=pk)

    if request.method == 'POST':
        testo = request.POST.get('testo', '').strip()
        voto = request.POST.get('voto')

        if testo and voto:
            Recensione.objects.update_or_create(
                escursionista=request.user,
                rifugio=rifugio,
                defaults={'testo': testo, 'voto': int(voto)}
            )
            messages.success(request, 'Recensione salvata!')

    return redirect('rifugio', pk=pk)

@gruppo_richiesto('Escursionista')
def modifica_profilo(request):
    if request.method == 'POST':
        request.user.first_name = request.POST.get('first_name', '')
        request.user.last_name = request.POST.get('last_name', '')
        request.user.email = request.POST.get('email', '')
        request.user.save()

        # Cambio password opzionale
        nuova_password = request.POST.get('nuova_password', '')
        if nuova_password:
            request.user.set_password(nuova_password)
            request.user.save()
            update_session_auth_hash(request, request.user)

        messages.success(request, 'Profilo aggiornato!')
        return redirect('passaporto')

    return render(request, 'rifugi/modifica_profilo.html')

@gruppo_richiesto('GestoreRifugio')
def dashboard_gestore(request):
    rifugi = Rifugio.objects.filter(gestore=request.user)
    for r in rifugi:
        aggiorna_posti_disponibili(r)
    prenotazioni = Prenotazione.objects.filter(
        rifugio__gestore=request.user,
        data_partenza__gt=date.today()
    ).select_related('escursionista', 'rifugio').order_by('-id')
    eventi = Evento.objects.filter(rifugio__gestore=request.user, data__gte=date.today()).prefetch_related('iscrizioni__escursionista').order_by('data')

    nuovo_rifugio_form = NuovoRifugioForm()
    evento_form = EventoForm()
    evento_form.fields['rifugio'].queryset = rifugi

    if request.method == 'POST':
        azione = request.POST.get('azione')

        if azione == 'aggiungi_rifugio':
            form = NuovoRifugioForm(request.POST, request.FILES)
            if form.is_valid():
                r = form.save(commit=False)
                r.gestore = request.user
                r.stato = 'in_attesa'
                r.save()
                messages.success(request, 'Rifugio inviato! Attendi l\'approvazione dell\'admin.')
            else:
                nuovo_rifugio_form = form

        elif azione == 'modifica_rifugio':
            pk = request.POST.get('rifugio_pk')
            r = get_object_or_404(Rifugio, pk=pk, gestore=request.user)
            form = ModificaRifugioForm(request.POST, instance=r)
            if form.is_valid():
                form.save()
                messages.success(request, 'Rifugio aggiornato!')

        elif azione == 'approva_prenotazione':
            pk = request.POST.get('prenotazione_pk')
            p = get_object_or_404(Prenotazione, pk=pk, rifugio__gestore=request.user)
            p.stato = 'approvata'
            p.save()
            # Scala i posti disponibili
            p.rifugio.posti_disponibili = max(0, p.rifugio.posti_disponibili - p.num_ospiti)
            p.rifugio.save()
            messages.success(request, 'Prenotazione approvata!')

        elif azione == 'rifiuta_prenotazione':
            pk = request.POST.get('prenotazione_pk')
            p = get_object_or_404(Prenotazione, pk=pk, rifugio__gestore=request.user)
            p.stato = 'rifiutata'
            p.save()
            messages.success(request, 'Prenotazione rifiutata.')

        elif azione == 'crea_evento':
            form = EventoForm(request.POST, request.FILES)
            form.fields['rifugio'].queryset = rifugi
            if form.is_valid():
                form.save()
                messages.success(request, 'Evento creato!')
            else:
                evento_form = form

        elif azione == 'modifica_evento':
            pk = request.POST.get('evento_pk')
            e = get_object_or_404(Evento, pk=pk, rifugio__gestore=request.user)
            form = EventoForm(request.POST, request.FILES, instance=e)  # ← manca instance=e!
            form.fields['rifugio'].queryset = rifugi
            if form.is_valid():
                form.save()
                messages.success(request, 'Evento aggiornato!')

        elif azione == 'elimina_evento':
            pk = request.POST.get('evento_pk')
            e = get_object_or_404(Evento, pk=pk, rifugio__gestore=request.user)
            e.delete()
            messages.success(request, 'Evento eliminato.')

        return redirect('dashboard_gestore')

    return render(request, 'rifugi/dashboard_gestore.html', {
        'rifugi': rifugi,
        'prenotazioni': prenotazioni,
        'eventi': eventi,
        'nuovo_rifugio_form': nuovo_rifugio_form,
        'evento_form': evento_form,
    })

@gruppo_richiesto('GuidaAlpina')
def dashboard_guida(request):
    itinerari = Itinerario.objects.filter(guida=request.user, data__gte=date.today()).prefetch_related('iscrizioni__escursionista').order_by('data')

    if request.method == 'POST':
        azione = request.POST.get('azione')

        if azione == 'crea_itinerario':
            form = ItinerarioForm(request.POST)
            if form.is_valid():
                it = form.save(commit=False)
                it.guida = request.user
                it.save()
                messages.success(request, 'Itinerario creato!')
            else:
                messages.error(request, 'Dati non validi: controlla i campi inseriti.')

        elif azione == 'modifica_itinerario':
            pk = request.POST.get('itinerario_pk')
            it = get_object_or_404(Itinerario, pk=pk, guida=request.user)
            form = ItinerarioForm(request.POST, instance=it)
            if form.is_valid():
                form.save()
                messages.success(request, 'Itinerario aggiornato!')
            else:
                messages.error(request, 'Dati non validi: controlla i campi inseriti.')

        elif azione == 'elimina_itinerario':
            pk = request.POST.get('itinerario_pk')
            it = get_object_or_404(Itinerario, pk=pk, guida=request.user)
            it.delete()
            messages.success(request, 'Itinerario eliminato.')

        return redirect('dashboard_guida')

    return render(request, 'rifugi/dashboard_guida.html', {'itinerari': itinerari})

@gruppo_richiesto('Admin')
def pannello_admin(request):

    rifugi_in_attesa = Rifugio.objects.filter(stato='in_attesa').select_related('gestore')

    # ─── Ricerca sui rifugi approvati ───────────────────────────
    cerca_admin = request.GET.get('cerca_admin', '').strip()
    rifugi_tutti = Rifugio.objects.filter(stato='approvato').order_by('-id')
    if cerca_admin:
        rifugi_tutti = rifugi_tutti.filter(
            Q(nome__icontains=cerca_admin) | Q(regione__icontains=cerca_admin)
        )

    now = timezone.now()

    now = timezone.now()
    escursionisti = User.objects.filter(groups__name='Escursionista')
    classifica = []
    for u in escursionisti:
        visite = Visita.objects.filter(
            escursionista=u,
            data_visita__year=now.year,
            data_visita__month=now.month
        ).select_related('rifugio')
        punti = sum(punti_rifugio(v.rifugio) for v in visite)
        classifica.append({
            'username': u.username,
            'email': u.email,
            'punti': punti,
            'num_visite': visite.count(),
        })
    classifica.sort(key=lambda x: x['punti'], reverse=True)

    if request.method == 'POST':
        azione = request.POST.get('azione')
        pk = request.POST.get('rifugio_pk')
        r = get_object_or_404(Rifugio, pk=pk)

        if azione == 'approva':
            r.stato = 'approvato'
            r.save()
            messages.success(request, f'{r.nome} approvato!')
        elif azione == 'rifiuta':
            r.delete()
            messages.success(request, 'Rifugio rifiutato ed eliminato.')
        elif azione == 'modifica_altitudine':
            nuova = request.POST.get('altitudine')
            if nuova:
                r.altitudine = int(nuova)
                r.save()
                messages.success(request, f'Altitudine di {r.nome} aggiornata!')
        elif azione == 'toggle_mensile':
            if r.mensile:
                r.mensile = False
                r.save()
                messages.info(request, f'{r.nome} rimosso dai rifugi mensili.')
            else:
                if Rifugio.objects.filter(mensile=True).count() >= 5:
                    messages.error(request, 'Hai già raggiunto il massimo di 5 rifugi mensili. Rimuovine uno prima di aggiungerne un altro.')
                else:
                    r.mensile = True
                    r.save()
                    messages.success(request, f'{r.nome} aggiunto ai rifugi mensili!')

        return redirect('pannello_admin')

    return render(request, 'rifugi/pannello_admin.html', {
            'rifugi_in_attesa': rifugi_in_attesa,
            'rifugi_tutti': rifugi_tutti,
            'num_mensili': Rifugio.objects.filter(mensile=True).count(),
            'classifica': classifica,
            'cerca_admin': cerca_admin,
        })