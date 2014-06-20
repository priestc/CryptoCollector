from django import forms

from wallet.models import wallet_classes

WALLET_CHOICES = [
    # ('btc', 'BTC - Bitcoin') for each currency
    (symbol, "%s - %s" % (symbol.upper(), kls.full_name)) for (symbol, kls) in wallet_classes.items()
]

class WalletForm(forms.Form):
    private_key = forms.CharField(max_length=64, help_text="optional", required=False)
    public_key = forms.CharField(max_length=64, help_text="optional", required=False)
    type = forms.ChoiceField(choices=WALLET_CHOICES)
    nickname = forms.CharField(required=False, help_text="optional")

    def make_wallet(self, owner):
        t = self.cleaned_data['type']
        Wallet = wallet_classes[t]
        public_key = self.cleaned_data['public_key']
        private_key = self.cleaned_data['private_key']

        if not public_key:
            public_key, private_key = Wallet.generate_new_keypair()

        wallet = Wallet.objects.create(
            owner=owner,
            public_key=public_key,
            private_key=private_key,
            name=self.cleaned_data['nickname'] or "My %s" % t.upper()
        )
