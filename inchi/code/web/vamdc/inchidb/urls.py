from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    (r'^db/', include('inchidb.db.urls')),
    (r'^api/', include('inchidb.api.urls')),
)
