swig -python -I/usr/local/include/inchi inchiapi.i
gcc -c inchiapi_wrap.c -I/usr/local/include/python2.7 -I/usr/local/lib/python2.7 -fPIC -I/usr/local/include/inchi
gcc -shared  -o _inchiapi.so inchiapi_wrap.o -linchi

