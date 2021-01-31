from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()


urlpatterns = patterns('',
    (r'^$', 'inchidb.db.views.homepage'),
    (r'^add/$', 'inchidb.db.views.add'),
    (r'^species/(?P<species_id>\S+)/$', 'inchidb.db.views.molecule'),
    (r'^duplicates/(?P<species_vamdc_inchikey>\S+)/$', 'inchidb.db.views.duplicates'),
    (r'^specieslist/$', 'inchidb.db.views.molecules'),

    # 2012-05-07 KWS Added an error redirect page.  Will add numbers to this to facilitate type of error.
    (r'^error/$', 'inchidb.db.views.error'),
)

