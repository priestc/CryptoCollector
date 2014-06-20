from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^$', 'main.views.home', name='home'),
    url(r'^wallet/', include('wallet.urls')),
    url(r'^admin/', include(admin.site.urls)),

    url(r'^logout$', 'django.contrib.auth.views.logout', name='logout')
)
