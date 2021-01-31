from django.conf.urls.defaults import *
#from piston.resource import Resource
from resource import Resource
from api.handlers import InchiHandler, AddInchiHandler

# Bypass authentication?
class CsrfExemptResource( Resource ):
    def __init__( self, handler, authentication = None ):
        super( CsrfExemptResource, self ).__init__( handler, authentication )
        self.csrf_exempt = getattr( self.handler, 'csrf_exempt', True )

inchi_resource = CsrfExemptResource( handler=InchiHandler )
addtodb_resource = CsrfExemptResource( handler=AddInchiHandler )

urlpatterns = patterns( '',
    url( r'^add/$', addtodb_resource ),
    url( r'^$', inchi_resource ),
    url( r'^(?P<expression>.*)$', inchi_resource ),
)


