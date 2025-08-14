// debug.h
#include <stdio.h>
#ifdef DEBUG
#define debug(...) fprintf(stdout, __VA_ARGS__)
#else
#define debug(...)
#endif