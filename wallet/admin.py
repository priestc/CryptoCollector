from django.contrib import admin
from models import (PeercoinWallet, BitcoinWallet, LitecoinWallet,
    FeathercoinWallet, DogecoinWallet, VertcoinWallet, NextWallet)

# Register your models here.

admin.site.register(PeercoinWallet)
admin.site.register(LitecoinWallet)
admin.site.register(BitcoinWallet)
admin.site.register(FeathercoinWallet)
admin.site.register(DogecoinWallet)
admin.site.register(VertcoinWallet)
admin.site.register(NextWallet)
