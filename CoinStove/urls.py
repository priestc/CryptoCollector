from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'main.views.home'),
    url(r'^accounts/login$', 'django.contrib.auth.views.login', {'template_name': 'login.html'}, name="login"),
    url(r'^accounts/logout$', 'django.contrib.auth.views.logout', {'next_page': '/'}, name='logout'),
    url(r'^accounts/register$', 'main.views.register', name="register"),
    url(r'^wallets/', include('wallet.urls')),
    url(r'^admin/', include(admin.site.urls)),
)

#https://ip.bitcointalk.org/?u=http%3A%2F%2Fi.imgur.com%2FnQRMdZl.png&t=541&c=vTVLe967IANlHw
