from django import forms
from django.contrib.auth.models import User, AbstractBaseUser

class CoinCollectorUser(AbstractBaseUser):
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
