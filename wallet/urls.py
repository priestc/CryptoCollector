from django.conf.urls import patterns, include, url

urlpatterns = patterns('wallet.views',
    url(r'^$', 'wallets', name='show_wallet'),
    url(r'^transactions$', 'get_transactions'),
    url(r'^value$', 'get_value'),
    url(r'^get_private_key', 'get_private_key'),
    url(r'^save_private_key', 'save_private_key'),
    url(r'^paper_wallet', 'paper_wallet'),
)
