from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from datetime import date
from django import forms
from .models import Rifugio, Visita, Timbro, Prenotazione, Recensione, Preferito

# ─── MIXIN PERMESSI ───────────────────────────────────────────────────────────

def gruppo_richiesto(nome_gruppo):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                from django.contrib.auth.views import redirect_to_login
                return redirect_to_login(request.get_full_path())
            if not request.user.groups.filter(name=nome_gruppo).exists() and not request.user.is_superuser:
                return render(request, '403.html', status=403)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

# ─── FORM REGISTRAZIONE ───────────────────────────────────────────────────────

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    
    class Meta(UserCreationForm.Meta):
        fields = ['username', 'email', 'password1', 'password2']

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
    rifugi_preferiti = []
    if request.user.is_authenticated:
        preferiti = Preferito.objects.filter(escursionista=request.user).select_related('rifugio')
        rifugi_preferiti = [p.rifugio for p in preferiti]

    rifugi_mensili = Rifugio.objects.filter(stato='approvato').order_by('-id')[:10]
    rifugi_casuali = Rifugio.objects.filter(stato='approvato').order_by('?')[:10]

    rifugi = Rifugio.objects.filter(stato='approvato')  # ← mancava questa riga!

    nome = request.GET.get('nome', '')
    regione = request.GET.get('regione', '')
    quota_min = request.GET.get('quota_min', '')
    quota_max = request.GET.get('quota_max', '')

    if nome:
        rifugi = rifugi.filter(nome__icontains=nome)
    if regione:
        rifugi = rifugi.filter(regione__icontains=regione)
    if quota_min:
        rifugi = rifugi.filter(altitudine__gte=quota_min)
    if quota_max:
        rifugi = rifugi.filter(altitudine__lte=quota_max)

    request.session['filtri'] = {
        'nome': nome,
        'regione': regione,
        'quota_min': quota_min,
        'quota_max': quota_max,
    }

    paginator = Paginator(rifugi, 10)
    page = request.GET.get('page')
    rifugi_paginati = paginator.get_page(page)

    return render(request, 'home.html', {
        'rifugi': rifugi_paginati,
        'rifugi_preferiti': rifugi_preferiti,
        'rifugi_mensili': rifugi_mensili,
        'rifugi_casuali': rifugi_casuali,  # ← nome coerente col template
        'nome': nome,
        'regione': regione,
        'quota_min': quota_min,
        'quota_max': quota_max,
    })

def rifugio(request, pk):
    r = get_object_or_404(Rifugio, pk=pk)
    recensioni = Recensione.objects.filter(rifugio=r).select_related('escursionista').order_by('-data')
    
    prenotazione = None
    if request.user.is_authenticated:
        prenotazione = Prenotazione.objects.filter(
            escursionista=request.user, rifugio=r
        ).first()

    return render(request, 'rifugi/rifugio.html', {
        'rifugio': r,
        'recensioni': recensioni,
        'prenotazione': prenotazione,
    })

def leaderboard(request):
    from django.contrib.auth.models import User
    
    escursionisti = User.objects.filter(groups__name='Escursionista')
    
    classifica = []
    for utente in escursionisti:
        visite = Visita.objects.filter(escursionista=utente).select_related('rifugio')
        punti = sum(v.rifugio.altitudine for v in visite)
        classifica.append({
            'username': utente.username,
            'punti': punti,
            'num_visite': visite.count(),
        })
    
    classifica.sort(key=lambda x: x['punti'], reverse=True)
 
    # Posizione dell'utente loggato
    posizione_utente = None
    punti_utente = 0
    if request.user.is_authenticated:
        for i, u in enumerate(classifica):
            if u['username'] == request.user.username:
                posizione_utente = i + 1
                punti_utente = u['punti']
                break
 
    return render(request, 'rifugi/leaderboard.html', {
        'classifica': classifica,
        'posizione_utente': posizione_utente,
        'punti_utente': punti_utente,
    })

# ─── VISTE RISTRETTE ──────────────────────────────────────────────────────────

@gruppo_richiesto('Escursionista')
def passaporto(request):
    visite = Visita.objects.filter(escursionista=request.user).select_related('rifugio', 'timbro').order_by('-data_visita')
    recensioni = Recensione.objects.filter(escursionista=request.user).select_related('rifugio').order_by('-data')
    prenotazioni = Prenotazione.objects.filter(escursionista=request.user)
    preferiti_qs = Preferito.objects.filter(escursionista=request.user)

    punti_totali = sum(v.rifugio.altitudine for v in visite)

    attivita = []
    for v in visite[:5]:
        attivita.append({'icona': 'landscape', 'testo': f'Hai visitato {v.rifugio.nome}', 'data': v.data_visita})
    for p in prenotazioni.order_by('-id')[:3]:
        attivita.append({'icona': 'calendar_today', 'testo': f'Hai prenotato {p.rifugio.nome}', 'data': p.data_arrivo})
    for f in preferiti_qs.order_by('-data')[:3]:
        attivita.append({'icona': 'bookmark', 'testo': f'Hai salvato {f.rifugio.nome} nei preferiti', 'data': f.data})
    attivita.sort(key=lambda x: str(x['data']), reverse=True)
    attivita = attivita[:8]

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
def preferiti(request):
    preferiti = Preferito.objects.filter(escursionista=request.user).select_related('rifugio')
    return render(request, 'rifugi/preferiti.html', {'preferiti': preferiti})

@gruppo_richiesto('Escursionista')
def prenota(request, pk):
    rifugio = get_object_or_404(Rifugio, pk=pk)
    if request.method == 'POST':
        data_arrivo = request.POST.get('data_arrivo')
        data_partenza = request.POST.get('data_partenza')
        num_ospiti = int(request.POST.get('num_ospiti', 1))

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

@gruppo_richiesto('GestoreRifugio')
def dashboard_gestore(request):
    rifugi = Rifugio.objects.filter(gestore=request.user)
    prenotazioni = Prenotazione.objects.filter(rifugio__gestore=request.user, stato='in_attesa')
    return render(request, 'rifugi/dashboard_gestore.html', {
        'rifugi': rifugi,
        'prenotazioni': prenotazioni,
    })

@gruppo_richiesto('Admin')
def pannello_admin(request):
    rifugi_in_attesa = Rifugio.objects.filter(stato='in_attesa')
    return render(request, 'rifugi/pannello_admin.html', {
        'rifugi_in_attesa': rifugi_in_attesa,
    })

