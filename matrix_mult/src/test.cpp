#include <hls_stream.h>
#include <ap_axi_sdata.h>

using namespace std;

typedef ap_axis<32,2,5,6> int_side_ch;

void matrixmul(hls:: stream<int_side_ch> &inStream , hls:: stream<int_side_ch> &outStream, int gain);

int main()
{
	hls:: stream<int_side_ch> inputStream;
	hls:: stream<int_side_ch> outputStream;

	for (int idx=0; idx<18; idx++)
	{
		int_side_ch val_in;
		val_in.data=idx;
		val_in.keep=1;
		val_in.strb=1;
		if(idx==17)
		val_in.last=1;
		else
		val_in.last=0;
		val_in.user=1;
		val_in.id=0;
		val_in.dest=0;

		inputStream<<val_in;
	}

	matrixmul(inputStream, outputStream, 1);

	for (int idx_out=0; idx_out<9; idx_out++)
	{
		int_side_ch val_out;
		outputStream.read(val_out);
		cout<<" matrix output val = "<< val_out.data;

	}


}
