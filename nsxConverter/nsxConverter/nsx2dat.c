#define _CRT_SECURE_NO_WARNINGS
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
//#include "Resampler.h"

#define BUF_SIZE 4096


#define T_NEURALSG 0x00
#define T_NEURALCD 0x01
#define T_BRSMPGRP 0x02
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
	unsigned long long Timestamp;
	unsigned long NumberOfDataPoints;
	unsigned long NumberOfDataBytes;
}NSXDataHeader;


int main(int argc, char** argv) 
{
	char inputFile[500];
	char outputFile[500];
	char buffer[BUF_SIZE];
	unsigned int data_package_offset, numchannel,samplingRate;
	unsigned long long int fileBytes;
	NSXMainHeader mainHeader;
	FILE *fh,*fh_w;
	char resample=0;
	if (argc == 1)
		return -1;
	
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

	int data_pkg_header = 0;
	char type_id[9] = "\0"; //convert to string
	memcpy(type_id, mainHeader.FileTypeID, 8);
	if (_strcmpi(type_id, "NEURALSG")==0)
	{
		data_pkg_header = T_NEURALSG;
	}
	else
	{
		if (_strcmpi(type_id, "NEURALCD")==0)
		{
			data_pkg_header =T_NEURALCD;
		}
		else
		{
			if (_strcmpi(type_id, "BRSMPGRP")==0)
			{
				data_pkg_header = T_BRSMPGRP;
			}
		}
	}

	data_package_offset = mainHeader.BytesInHeaders[0] | mainHeader.BytesInHeaders[1] << 8 | mainHeader.BytesInHeaders[2] << 16 | mainHeader.BytesInHeaders[3] << 24;
	numchannel = mainHeader.ChannelCount[0] | mainHeader.ChannelCount[1] << 8 | mainHeader.ChannelCount[2] << 16 | mainHeader.ChannelCount[3] << 24;
	fseek(fh, data_package_offset, SEEK_SET);
	long long int rdcnt = 0;
	long long int current_pos;

	while (!feof(fh))
	{
		NSXDataHeader Header;
		unsigned long Npoints;
		long long Datapoints;
		if (decodeDataHeader(&mainHeader, &Header, fh, data_pkg_header) == -1)
		{
			break;
		}
		Datapoints = Header.NumberOfDataBytes;
		current_pos = ftell(fh);

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
			//Run direct convert without resampling				
			fwrite(buffer, 1, rdcnt, fh_w);
			Datapoints -=rdcnt;
			if (feof(fh))
				break;
		}
	}
	fclose(fh);
	fclose(fh_w);
	return 0;
}

int decodeDataHeader(NSXMainHeader *mainHeader,NSXDataHeader *header, FILE *f, int type)
{

	unsigned long long timestamp;
	unsigned long long datacount;
	unsigned long long curr_location,file_size;
	unsigned long data_package_offset = mainHeader->BytesInHeaders[0] | mainHeader->BytesInHeaders[1] << 8 | mainHeader->BytesInHeaders[2] << 16 | mainHeader->BytesInHeaders[3] << 24;
	unsigned int numchannel = mainHeader->ChannelCount[0] | mainHeader->ChannelCount[1] << 8 | mainHeader->ChannelCount[2] << 16 | mainHeader->ChannelCount[3] << 24;
	curr_location = ftell(f);
	fseek(f, 0, SEEK_END);
	file_size = ftell(f);
	fseek(f, curr_location, SEEK_SET);//restore file pointer

	if (curr_location == file_size)
	{
		return -1; //return -1 if reach to end of file stream
	}
	if (type == T_NEURALSG)
	{
		header->Header = 0x01;
		header->NumberOfDataPoints = (file_size - curr_location) / numchannel / 2;
	}
	else
	{
		if (type == T_NEURALCD)
		{
			unsigned char temp[9];
			fread(temp, 1, 9, f);
			header->Header = temp[0];
			header->Timestamp= temp[1] | temp[2] << 8 | temp[3] << 16 | temp[4] << 24;
			header->NumberOfDataPoints = temp[5] | temp[6] << 8 | temp[7] << 16 | temp[8] << 24;
		}
		else
		{
			if (type == T_BRSMPGRP)
			{
				unsigned char temp[13];
				fread(temp, 1, 13, f);
				header->Header = temp[0];
				header->Timestamp = temp[1] | temp[2] << 8 | temp[3] << 16 | temp[4] << 24 | temp[5]<<32 | temp[6] << 40 | temp[7] << 48 | temp[8] << 56;
				header->NumberOfDataPoints = temp[9] | temp[10] << 8 | temp[11] << 16 | temp[12] << 24;
			}
		}
		if (header->Header != 0x01) //for bug that not writting back header after recording
		{
			header->Header = 0x01;
			header->NumberOfDataPoints = (file_size - curr_location) / numchannel / 2;
			fseek(f, curr_location, SEEK_SET);//restore file pointer
		}

	}
	header->NumberOfDataBytes = header->NumberOfDataPoints * 2 * numchannel;
	return 0;
}