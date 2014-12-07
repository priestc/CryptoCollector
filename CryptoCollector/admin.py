from django.contrib import admin
from models import KeyPair

# Register your models here.
class KeyPairAdmin(admin.ModelAdmin):
    list_display = ['owner', 'crypto', 'address']

admin.site.register(KeyPair, KeyPairAdmin)
