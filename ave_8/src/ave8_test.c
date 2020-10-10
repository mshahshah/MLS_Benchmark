			// ifdef pre-compiler directive to separate SW from HW C
#include <stdio.h>
#include <stdlib.h>
 int ave8(int buffer[8]);
int main(){

    FILE *fp_i, *fp_o;
    int i;
    int buffer[8]  = {0, 0, 0, 0, 0, 0, 0, 0};

    if((fp_i = fopen("indata.txt", "r")) == NULL){
	printf(" \"indata.txt \" could not be opened.\n");
	exit(1);
    }
    if((fp_o = fopen("outdata.txt", "w")) == NULL){
	printf(" \"outdata.txt \" could not be opened.\n");
	exit(1);
    }

    for (;;){

    	if (fscanf(fp_i, "%d", &in0) == EOF) break;
	ave8(buffer);	    // Main computational function
	fprintf(fp_o, "%d\n", out0);
    }

    fclose(fp_i);
    fclose(fp_o);
}
