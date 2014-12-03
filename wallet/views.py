import json
import datetime
from collections import OrderedDict

from moneywagon import get_current_price

from django.template.response import TemplateResponse
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from forms import WalletForm, SendMoneyForm
from models import Transaction, KeyPair

class TransactionJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Transaction):
            return super(DateTimeJSONEncoder, self).default(obj.txdata)
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()
        else:
            return super(DateTimeJSONEncoder, self).default(obj)

@login_required
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
            return HttpResponseRedirect("/wallets/")

    keypairs = KeyPair.objects.filter(owner__id=request.user.id)

    return TemplateResponse(request, 'wallet.html', {
        'keypairs': keypairs,
        'no_wallets': keypairs.exists(),
        'new_wallet_form': form,
    })

@login_required
def get_transactions(request):
    """
    API call for getting transactions for a wallet.
    Called by front end browser ajax, returns JSON.
    """
    address = request.GET['address']
    fiat = request.GET.get('fiat', 'usd')
    keypair = KeyPair.objects.get(pk=pk, owner__id=request.user.id)
    transactions = keypair.get_transactions()
    return HttpResponse(json.dumps(j, cls=TransactionJSONEncoder), content_type="application/json")

@login_required
def get_value(request):
    """
    API call for getting the most recent price for a wallet.
    All requests via this way bypass cache. Data is always most fresh.
    """
    address = request.GET['address']
    keypair = KeyPair.objects.get(pk=pk, owner__id=request.user.id)

    j = wallet.price_json(hard_refresh=False)
    return HttpResponse(j, content_type="application/json")

def get_exchange_rate(request):
    crypto = request.GET['crypto']
    fiat = request.GET['fiat']
    return HttpResponse(get_current_price(crypto, fiat), content_type="application/json")

@login_required
def get_private_key(request):
    address = request.GET['address']
    keypair = KeyPair.objects.get(pk=pk, owner__id=request.user.id)
    return HttpResponse(keypair.private_key, content_type="text/plain")

@login_required
def save_private_key(request):
    symbol, pk = request.POST['js_id'].split('-')
    wallet = wallet_classes[symbol].objects.filter(
        pk=pk,
        owner__id=request.user.id
    ).get()
    wallet.private_key = request.POST['private_key']
    wallet.save()
    messages.info(request, "Private key succesfully added to <strong>%s</strong>" % wallet.name)
    return HttpResponseRedirect("/wallets/")

@login_required
def paper_wallet(request):
    """
    Either pass in a single jsid of a wallet, or pass in nothing to generate
    a page with all the paper wallets from your account. It skips wallets
    that do not have a private key, and that have no value stored in them.
    """
    js_id = request.GET.get('js_id', None)
    if js_id:
        symbol, pk = js_id.split("-")
        wallet = wallet_classes[symbol].objects.get(
            pk=pk,
            owner__id=request.user.id
        )
        wallets = [wallet]
    else:
        wallets = []
        for symbol, Wallet in wallet_classes.items():
            wals = list(
                Wallet.objects.filter(owner__id=request.user.id)
                .exclude(private_key='')
            )
            wallets.extend(wals)

    return TemplateResponse(request, 'paper_wallet.html', {
        'wallets': wallets,
    })

@login_required
def send_money(request):
    currency = request.GET.get('currency', None)
    fiat = request.GET.get('fiat', None)
    form = SendMoneyForm(initial={'currency': currency})

    if request.POST:
        form = SendMoneyForm(request.POST)
        if form.is_valid():
            form.execute()
            return HttpResponseRedirect("/wallets/")

    conversion_rate = wallet_classes[currency].get_fiat_exchange(fiat)

    return TemplateResponse(request, 'send_money.html', {
        'form': form,
        'currency': currency,
        'conversion_rate': conversion_rate,
        'fiat': fiat,
    })
