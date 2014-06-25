from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^$', 'django.contrib.auth.views.login', {'template_name': 'home.html'}),
    url(r'^wallets/', include('wallet.urls')),
    url(r'^admin/', include(admin.site.urls)),

    url(r'^logout$', 'django.contrib.auth.views.logout', {'next_page': '/'}, name='logout'),
)
