from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group
from django.core.paginator import Paginator
from django import forms
from .models import Rifugio

# Form di registrazione con email
class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    
    class Meta(UserCreationForm.Meta):
        fields = ['username', 'email', 'password1', 'password2']

# Vista registrazione
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

# Home page
def home(request):
    rifugi = Rifugio.objects.filter(stato='approvato')

    # Ricerca
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

    # Salva filtri in sessione
    request.session['filtri'] = {
        'nome': nome,
        'regione': regione,
        'quota_min': quota_min,
        'quota_max': quota_max,
    }

    # Paginazione
    paginator = Paginator(rifugi, 10)
    page = request.GET.get('page')
    rifugi_paginati = paginator.get_page(page)

    return render(request, 'home.html', {
        'rifugi': rifugi_paginati,
        'nome': nome,
        'regione': regione,
        'quota_min': quota_min,
        'quota_max': quota_max,
    })

def rifugio(request, pk):
    r = Rifugio.objects.get(pk=pk)
    return render(request, 'rifugi/rifugio.html', {'rifugio': r})