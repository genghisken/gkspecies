%module inchiapi
%{
#include "inchi_api.h"
%}

// Required because the GetStdINCHIKeyFromStdINCHI function returns result through string buffer
%include <cstring.i>
%cstring_bounded_output(char *szINCHIKey, 28);
%cstring_bounded_output(char *szXtra1, 65);
%cstring_bounded_output(char *szXtra2, 65);

// Include the header file with above prototypes
%include "inchi_api.h"

