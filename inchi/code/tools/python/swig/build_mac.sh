swig -python -I/usr/local/include/inchi inchiapi.i
gcc -c inchiapi_wrap.c -I/System/Library/Frameworks/Python.framework/Versions/2.7/include/python2.7 -fPIC -I/usr/local/include/inchi
gcc -shared  -o _inchiapi.so inchiapi_wrap.o -linchi `python-config --ldflags`

