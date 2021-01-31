# Code copied to convert the error code into JSON
from django.http import HttpResponse
import piston.emitters
import piston.handler
import piston.resource
import piston.utils
class Resource(piston.resource.Resource):
    def error_handler(self, e, request, meth, em_format):
        if isinstance(e, piston.utils.FormValidationError):
            return self.form_validation_response_formatted(request, e, em_format)
        return super(Resource, self).error_handler(e, request, meth, em_format)
    def form_validation_response_formatted(self, request, e, em_format):
        try:
            emitter, ct = piston.emitters.Emitter.get(em_format)
            fields = self.handler.fields
        except ValueError:
            result = piston.utils.rc.BAD_REQUEST
            result.content = "Invalid output format specified '%s'." % em_format
            return result
        serialized_errors = dict((key, [unicode(v) for v in values])
                                for key,values in e.form.errors.items())
        srl = emitter(serialized_errors, piston.handler.typemapper, self.handler, fields, False)
        stream = srl.render(request)
        resp = HttpResponse(stream, mimetype=ct, status=400)
        return resp
