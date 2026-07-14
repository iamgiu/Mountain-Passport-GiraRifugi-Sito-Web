"""
URL configuration for girarifugi project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Lista principale che rappresenta gli URl del sito alle relative funzioni/viste
# Quando l'utente va su www.sito.com/admin/ Django apre il pannello di amministrazione 
# Include il sistema di autenticazione di Django, quindi gestisce in automatico i login/logout
# La stringa vuota indica la pagina iniziale e poi delega la gestione di tutti gli altri percorsi al file urls.py dell'applicazione interna
# Infine dice a Django come trovare e mostrare i file multimediali
urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', include('rifugi.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
