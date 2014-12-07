from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'CryptoCollector.views.home'),
    url(r'^accounts/login$', 'django.contrib.auth.views.login', {'template_name': 'login.html'}, name="login"),
    url(r'^accounts/logout$', 'django.contrib.auth.views.logout', {'next_page': '/'}, name='logout'),
    url(r'^accounts/register$', 'CryptoCollector.views.register', name="register"),
    url(r'^wallets', 'CryptoCollector.views.wallets', name='show_wallet'),
    url(r'^send_money', 'CryptoCollector.views.send_money', name="send_money"),
    url(r'^transactions', 'CryptoCollector.views.get_transactions'),
    url(r'^value$', 'CryptoCollector.views.get_value'),
    url(r'^get_exchange_rate', 'CryptoCollector.views.get_exchange_rate'),
    url(r'^get_private_key', 'CryptoCollector.views.get_private_key'),
    url(r'^save_private_key', 'CryptoCollector.views.save_private_key'),
    url(r'^paper_wallet', 'CryptoCollector.views.paper_wallet'),

    url(r'^admin/', include(admin.site.urls)),
)

#https://ip.bitcointalk.org/?u=http%3A%2F%2Fi.imgur.com%2FnQRMdZl.png&t=541&c=vTVLe967IANlHw
