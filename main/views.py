from django.template.response import TemplateResponse
from django.http import HttpResponseRedirect
from django.contrib.auth import authenticate, login
from wallet.models import wallet_classes
from main.forms import RegistrationForm

def home(request):
    return TemplateResponse(request, "home.html", {
        'supported_currencies': [
            (crypto_symbol, cls.full_name) for crypto_symbol, cls in wallet_classes.items()
        ]
    })

def register(request):
    form = RegistrationForm()
    if request.POST:
        form = RegistrationForm(request.POST)
        if form.is_valid():
            username, password = form.save()
            user = authenticate(username=username, password=password)
            login(request, user)
            return HttpResponseRedirect("/wallets/")

    return TemplateResponse(request, "register.html", {
        'form': form
    })
