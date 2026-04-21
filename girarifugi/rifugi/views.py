from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group
from django import forms

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
            # Assegna automaticamente al gruppo Escursionista
            gruppo = Group.objects.get(name='Escursionista')
            user.groups.add(gruppo)
            return redirect('/accounts/login/')
    else:
        form = RegisterForm()
    return render(request, 'registration/register.html', {'form': form})

# Home page (per ora lista rifugi approvati)
def home(request):
    return render(request, 'home.html')