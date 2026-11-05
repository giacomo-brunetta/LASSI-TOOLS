/* Preserve the upstream float arithmetic and serial execution path (mode 1). */
#include <stdlib.h>
#include <math.h>
#include <omp.h>
#include "define.c"
#include "ecc.c"
#include "cam.c"
#include "fin.c"
#include "master.c"
#include "embedded_fehlberg_7_8.c"
#include "solver.c"
