/**************************************************
**
**   ave8.c
**
** Description: The following program computes the average 
**                     of the 8 numbers being read
**
****************************************************/
#include <stdio.h>
#include <stdlib.h>
	
int  in0;
int out0;

/* Global variables */






   int ave8(int buffer[8]){

   /* Local variables declaration */
    int  out0_v, sum,  i; 


 /* Shift data to accommodate new input to be read */
    L1:    for (i = 7; i > 0; i--) {
            buffer[i] = buffer[i- 1];
        }
	
  /* Read new input into buffer */
    buffer[0] = in0;

  /* Set first element of sum to compute the average => can save 1 loop iteration */
    sum= buffer[0]; 	
        
   /* Add up all the numbers in the buffer */
    L2:  for (i= 1; i< 8; i++) {
            sum += buffer[i]; 	
        }

 /* Compute the average by dividing by 8 -> In HW  a divide by 8 (/8) = shift 3 times */
        out0_v= sum / 8; 

  /* Output the newly computed average to the output port */
        out0 = out0_v;	

    return (0); 	
}

/*------------------------------------------------------  
 * ANSI-C test bench 
 *-----------------------------------------------------  */
			// ifdef pre-compiler directive to separate SW from HW C
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


