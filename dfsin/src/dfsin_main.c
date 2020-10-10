#include <stdio.h>
#include "softfloat.h"
#include "milieu.h"
//#include "softfloat.c"
//#include "dfsin.c"


int main ()
{
  int main_result;
  int i;
      main_result = 0;
      for (i = 0; i < N; i++)
	{
	  float64 result;
	  result = local_sin (test_in[i]);
	  main_result += (result != test_out[i]);

	  printf
	    ("input=%016llx expected=%016llx output=%016llx (%lf)\n",
	     test_in[i], test_out[i], result, ullong_to_double (result));
	}
      printf ("%d\n", main_result);
      return main_result;
    }
