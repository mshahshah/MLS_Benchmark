//*****************************************************************************
// (c) Copyright 2009 - 2012 Xilinx, Inc. All rights reserved.
//
// This file contains confidential and proprietary information
// of Xilinx, Inc. and is protected under U.S. and
// international copyright and other intellectual property
// laws.
//
// DISCLAIMER
// This disclaimer is not a license and does not grant any
// rights to the materials distributed herewith. Except as
// otherwise provided in a valid license issued to you by
// Xilinx, and to the maximum extent permitted by applicable
// law: (1) THESE MATERIALS ARE MADE AVAILABLE "AS IS" AND
// WITH ALL FAULTS, AND XILINX HEREBY DISCLAIMS ALL WARRANTIES
// AND CONDITIONS, EXPRESS, IMPLIED, OR STATUTORY, INCLUDING
// BUT NOT LIMITED TO WARRANTIES OF MERCHANTABILITY, NON-
// INFRINGEMENT, OR FITNESS FOR ANY PARTICULAR PURPOSE; and
// (2) Xilinx shall not be liable (whether in contract or tort,

// liability) for any loss or damage of any kind or nature
// related to, arising under or in connection with these
// materials, including for any direct, or any indirect,
// special, incidental, or consequential loss or damage
// (including loss of data, profits, goodwill, or any type of
// loss or damage suffered as a result of any action brought
// by a third party) even if such damage or loss was
// reasonably foreseeable or Xilinx had been advised of the
// possibility of the same.
//
// CRITICAL APPLICATIONS
// Xilinx products are not designed or intended to be fail-
// safe, or for use in any application requiring fail-safe
// performance, such as life-support or safety devices or
// systems, Class III medical devices, nuclear facilities,
// applications related to the deployment of airbags, or any
// other applications that could lead to death, personal
// injury, or severe property or environmental damage
// (individually and collectively, "Critical
// Applications"). Customer assumes the sole risk and
// liability of any use of Xilinx products in Critical
// Applications, subject only to applicable laws and
// regulations governing limitations on product liability.
//
// THIS COPYRIGHT NOTICE AND DISCLAIMER MUST BE RETAINED AS
// PART OF THIS FILE AT ALL TIMES.
//
//*****************************************************************************
//   ____  ____
//  /   /\/   /
// /___/  \  /    Vendor: Xilinx
// \   \   \/     Version: %version
//  \   \         Application: AutoESL
//  /   /         Filename: matrixmul.cpp
// /___/   /\     Date Last Modified: $Date: 2012/3/30 18:53:07 $
// \   \  /  \    Date Created: Fri Mar 30 2012
//  \___\/\___\
//
//Device: All
//Design Name: matrixmul
//Purpose:
//    This is a C++ version of a matrix multiplier example.
//Reference:
//Revision History:
//*****************************************************************************

/*
#include <cmath>
#include <iostream>

*/
#include <hls_stream.h>
#include <ap_axi_sdata.h>
#include <math.h>
#include <ap_int.h>
#include <iostream>

using namespace std;

#define ROW 3
#define COL 3

typedef ap_axis <32,2,5,6> int_side_ch;

unsigned int a[3][3]={
		  {0, 0, 0},
		  {0, 0, 0},
		  {0, 0, 0}
		};
unsigned int b[3][3]={
		  {0, 0, 0},
		  {0, 0, 0},
		  {0, 0, 0}
		};

unsigned int res[3][3]={
		  {0, 0, 0},
		  {0, 0, 0},
		  {0, 0, 0}
		};

unsigned int my_array[9]={1,2,3,4,5,6,7,8,9}; //     0,0,0,0,0,0,0,0,0};

void matrixmul(hls:: stream<int_side_ch> &inStream , hls:: stream<int_side_ch> &outStream, int gain)
{
#pragma HLS INTERFACE s_axilite port=return bundle=CRTL_BUS
#pragma HLS INTERFACE s_axilite port=gain bundle=CRTL_BUS
	int_side_ch val_in;
	int_side_ch val_out;
	int r=0,c=0, r1=0, c1=0;


	L1:for(int i = 0; i < 18; i++)
	{
		val_in= inStream.read();

		if (i<9)
		{
			a[r][c]=(int)val_in.data;


			if (c==2)
			{
				c=0;
				r++;
			}
			else
			{
				c++;
			}

			if (r==9 && c==9)
			{
				r=0;
				c=0;
			}

		}

		else if (i>=9)
				{
					b[r1][c1]=(int)val_in.data ;


					if (c1==2)
					{
						c1=0;
						r1++;
					}
					else
					{
						c1++;
					}



				}


	}

  // Iterate over the rows of the A matrix

	int sum=0;
  Row: for(int j = 0; j < 3; j++) {
    // Iterate over the columns of the B matrix
    Col: for(int i = 0; i < 3; i++) {
      // Do the inner product of a row of A and col of B
      sum = 0;
      Product: for(int k = 0; k < 3; k++) {
     //  #pragma HLS UNROLL
        sum = sum + a[i][k] * b[k][j];
      }

      res[i][j]= sum;
    }
  }

  cout<<" Matrix A"<<endl;
  Aout:for(int i = 0; i < 3; i++) {
       // Iterate over the columns of the B matrix
       for(int j = 0; j < 3; j++) {
         cout<< a[i][j]<<" ";

         }
       	  cout<<endl;
       }


  cout<<" Matrix B"<<endl;
   Bout: for(int i = 0; i < 3; i++) {
         // Iterate over the columns of the B matrix
         for(int j = 0; j < 3; j++) {
           cout<< b[i][j]<<" ";

           }
         	  cout<<endl;
         }

    cout<<" Matrix result"<<endl;

    int cnt =0;
    Res_out_sw1: for(int i = 0; i < 3; i++) {
      // Iterate over the columns of the B matrix
	  Res_out_sw2:      for(int j = 0; j < 3; j++) {
        cout<< res[i][j]<<" ";

        my_array[cnt]= res[i][j];
        cnt++;

        }
      	  cout<<endl;
      }

  Res_out_hw:for(int i = 0; i < 9; i++)
  {
		  val_out.keep= val_in.keep;
		  val_out.strb= val_in.strb;
		  val_out.user= val_in.user;
		  val_out.dest= val_in.dest;
		  val_out.id= val_in.id;

		  if (i==8)  //&& j==2)
		  {
			  val_out.last=val_in.last;
		  }
		  else
		  {
			  val_out.last=0;
		  }



		  val_out.data= my_array[i];
		  outStream.write(val_out);
  }

 return;
}


