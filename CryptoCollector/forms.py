from django import forms
from django.contrib.auth.models import User, AbstractBaseUser
from django.conf import settings

FEE_CHOICES = [
    (0, 'nothing'),
    (1, 'penny'),
    (2, 'nickel'),
    (3, 'dollar')
]

class WalletForm(forms.Form):
    """
    For creating/generating new keypairs.
    """
    private_key = forms.CharField(max_length=64, help_text="optional", required=False)
    public_key = forms.CharField(max_length=64, help_text="optional", required=False)
    type = forms.ChoiceField(choices=settings.SUPPORTED_CRYPTOS)
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

class SendMoneyForm(forms.Form):
    currency = forms.CharField(widget=forms.HiddenInput)
    amount = forms.CharField(initial=0, widget=forms.TextInput(attrs={'class': 'small-numeric'}))
    #saved_addresses_selection = forms.ModelChoiceField(queryset=SavedRecipientAddress.objects.none())
    target_address = forms.CharField()
    save_target_address_label = forms.CharField()
    miner_fee = forms.ChoiceField(choices=FEE_CHOICES)

    def execute(self):
        Wallet = wallet_classes[self.cleaned_data['currency']]
        target_address = self.cleaned_data['target_address']
        target_address_label = self.cleaned_data['target_address_label']

        Wallet.send_transaction(
            amount=self.cleaned_data['amount'],
            target=target_address
        )


class CryptoCollectorUser(AbstractBaseUser):
    pass

class RegistrationForm(forms.Form):
    password = forms.CharField(
        widget=forms.PasswordInput()
    )

    password2 = forms.CharField(
        label="Password Again",
        widget=forms.PasswordInput()
    )

    username = forms.CharField()

    email = forms.CharField(
        widget=forms.EmailInput()
    )
    def clean(self):
        cleaned_data = super(RegistrationForm, self).clean()
        if cleaned_data['password2'] != cleaned_data['password']:
            raise forms.ValidationError('Passwords must match')
        return cleaned_data

    def save(self):
        username = self.cleaned_data['username']
        password = self.cleaned_data['password']

        user = User.objects.create(
            username=username,
            email=self.cleaned_data['email']
        )

        user.set_password(password)
        user.save()
        return username, password
