#define _CRT_SECURE_NO_WARNINGS
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "Resampler.h"

#define BUF_SIZE 262144

typedef struct
{
	char FileTypeID[8];
	unsigned char FileSpec[2];
	unsigned char BytesInHeaders[4];
	char Label[16];
	char Comment[256];
	unsigned char Period[4];
	unsigned char TimeResolution[4];
	char TimeOrigin[16];
	unsigned char ChannelCount[4];
}NSXMainHeader;

typedef struct
{
	char Header;
	unsigned char Timestamp[4];
	unsigned char NumberOfDataPoints[4];
}NSXDataHeader;
int main(int argc, char** argv) 
{
	char inputFile[500];
	char outputFile[500];
	char buffer[BUF_SIZE];
	unsigned int dataoffset, numchannel,samplingRate;
	unsigned long long int fileBytes;
	NSXMainHeader mainHeader;
	FILE *fh,*fh_w;
	char resample=0;
	if (argc == 1)
		return -1;

	if (argc >= 3)
		resample = *argv[2]-'0';
	
	strcpy(inputFile, argv[1]);

	int len;
	len = strlen(inputFile);
	strncpy(outputFile, inputFile, len - 4);
	outputFile[len - 4] = '\0';
	strcat(outputFile, ".dat\0");
	
	fh = fopen(inputFile, "rb+");
	fh_w = fopen(outputFile, "wb+");

	fseek(fh, 0, SEEK_END);
	fileBytes = ftell(fh);

	fseek(fh, 0, SEEK_SET);
	fread(&mainHeader, sizeof(mainHeader), 1, fh);
	dataoffset = mainHeader.BytesInHeaders[0] | mainHeader.BytesInHeaders[1] << 8 | mainHeader.BytesInHeaders[2] << 16 | mainHeader.BytesInHeaders[3] << 24;
	numchannel = mainHeader.ChannelCount[0] | mainHeader.ChannelCount[1] << 8 | mainHeader.ChannelCount[2] << 16 | mainHeader.ChannelCount[3] << 24;
	fseek(fh, dataoffset, SEEK_SET);
	long long int rdcnt = 0;
	long long int current_pos;

	// Create the Resampler
	const int filterLength = 64;
	const float filter[filterLength] = { 0, 0, 0, -9.5461e-19, -0.0010152, -0.0014343, 2.4726e-18, 0.0025517, 0.0032727, -4.6593e-18, -0.0051034, -0.0062423, 7.4759e-18, 0.0090528, 0.010765, -1.0789e-17, -0.014935, -0.017458, 1.4376e-17, 0.023615, 0.027381, -1.7948e-17, -0.036797, -0.042772, 2.1181e-17, 0.058682, 0.069683, -2.3762e-17, -0.10366, -0.13253, 2.5428e-17, 0.2731, 0.5503, 0.66707, 0.5503, 0.2731, 2.5428e-17, -0.13253, -0.10366, -2.3762e-17, 0.069683, 0.058682, 2.1181e-17, -0.042772, -0.036797, -1.7948e-17, 0.027381, 0.023615, 1.4376e-17, -0.017458, -0.014935, -1.0789e-17, 0.010765, 0.0090528, 7.4759e-18, -0.0062423, -0.0051034, -4.6593e-18, 0.0032727, 0.0025517, 2.4726e-18, -0.0014343, -0.0010152, -9.5461e-19 };
	Resampler<uint16_t, uint16_t, float> *h_res[512];
	for (int i = 0; i < numchannel; i++)
	{
		h_res[i] = new Resampler<uint16_t, uint16_t, float>(2, 3, (float*)filter, filterLength);
	}
	while (!feof(fh))
	{
		NSXDataHeader Header;
		unsigned long Npoints;
		long long Datapoints;
		fread(&Header, sizeof(Header), 1, fh);
		Npoints = Header.NumberOfDataPoints[0] | Header.NumberOfDataPoints[1] << 8 | Header.NumberOfDataPoints[2] << 16 | Header.NumberOfDataPoints[3] << 24;
		Datapoints = Npoints * 2 * numchannel;
		current_pos = ftell(fh);
		if (Datapoints == 0 && current_pos < fileBytes)
			Datapoints = ((fileBytes - Datapoints) / (2 * numchannel)) * (2 * numchannel);


		
		while (Datapoints > 0)
		{
			int Nread;
			if (Datapoints >= BUF_SIZE)
			{
				Nread = (BUF_SIZE/ (2 * numchannel))*(2 * numchannel); //make sure read same length for all channels
			}
			else
			{
				Nread = Datapoints;
			}
			rdcnt = fread(buffer, 1, Nread, fh);
			current_pos = ftell(fh);
			if (resample == 0)
			{
				//Run direct convert without resampling				
				fwrite(buffer, 1, rdcnt, fh_w);
			}
			else
			{
				//Run resampling
				uint8_t res_buf[BUF_SIZE];
				int data_ptr=0;
				int out_ptr = 0;
				while (data_ptr < rdcnt)
				{
					for (int i = 0; i < numchannel; i++)
					{
						// calc size of output
						int resultsCount = h_res[i]->neededOutCount(1);
						// run filtering
						int numSamplesComputed = h_res[i]->apply((uint16_t*)&buffer[data_ptr],
							1, (uint16_t*)&res_buf[out_ptr*2], resultsCount);
						data_ptr += 2;
						out_ptr  += resultsCount;
						
					}
				}
				fwrite(res_buf, 1, out_ptr * 2, fh_w);
			}
			Datapoints -=rdcnt;
			if (feof(fh))
				break;
		}
	}
	for (int i = 0; i < numchannel; i++)
	{
		delete[] h_res[i];
	}
	fclose(fh);
	fclose(fh_w);
	return 0;
}