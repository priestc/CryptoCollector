import json
from collections import OrderedDict

from django.template.response import TemplateResponse
from django.http import HttpResponse
from django.contrib import messages
from models import wallet_classes
from forms import WalletForm

def wallets(request):
    """
    Show all wallets for logged in user.
    """
    form = WalletForm()
    if request.POST:
        form = WalletForm(request.POST)
        if form.is_valid():
            try:
                form.make_wallet(request.user)
            except NotImplementedError:
                curr = form.cleaned_data['type'].upper()
                messages.error(request, "Can't create wallets of type %s yet" % curr)

    wallets = OrderedDict()
    for symbol, Wallet in wallet_classes.items():
        wallets[symbol] = Wallet.objects.filter(owner__id=request.user.id)
    
    return TemplateResponse(request, 'wallet.html', {
        'wallets_for_all_currencies': wallets,
        'new_wallet_form': form,
    })

def get_transactions(request):
    """
    API call for getting transactions for a wallet.
    Called by front end browser ajax, returns JSON.
    """
    symbol, pk = request.GET['js_id'].split('-')
    wallet = wallet_classes[symbol].objects.filter(pk=pk).filter(
        owner__id=request.user.id
    ).get()
    j = json.dumps(wallet.get_transactions())
    return HttpResponse(j, content_type="application/json")

def get_value(request):
    """
    API call for getting the most recent price for a wallet.
    Al requests via this way bypass cache.
    """
    symbol, pk = request.GET['js_id'].split('-')
    wallet = wallet_classes[symbol].objects.filter(pk=pk).filter(
        owner__id=request.user.id
    ).get()
    res = {
        'fiat_exchange': wallet.get_fiat_exchange(hard_refresh=True),
        'wallet_value': wallet.get_value(hard_refresh=True),
        'fiat_value': wallet.get_fiat_value(),
    }
    return HttpResponse(json.dumps(res), content_type="application/json")


def get_private_key(request):
    symbol, pk = request.GET['js_id'].split('-')
    wallet = wallet_classes[symbol].objects.filter(pk=pk).filter(
        owner__id=request.user.id
    ).get()
    return HttpResponse(wallet.private_key, content_type="text/plain")
