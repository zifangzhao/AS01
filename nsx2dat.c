#define _CRT_SECURE_NO_WARNINGS
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define BUF_SIZE 4096

int main(int argc, char** argv) 
{
	char inputFile[500];
	char outputFile[500];
	char buffer[BUF_SIZE];
	unsigned int dataoffset, numchannel,samplingRate;
	unsigned long long int fileBytes;
	FILE *fh,*fh_w;
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

	fseek(fh, 10, SEEK_SET);
	fread(&dataoffset, 4, 1,fh);
	dataoffset += 9;

	fseek(fh, 290, SEEK_SET);
	fread(&samplingRate, 4, 1, fh);

	fseek(fh, 310, SEEK_SET);
	fread(&numchannel, 4, 1, fh);

	fseek(fh, dataoffset, SEEK_SET);
	long long int rdcnt = 1;
	long long int current_pos;
	while (!feof(fh))
	{
		char Header;
		unsigned long long Timestamp;
		unsigned long Npoints;
		fread(&Header,1,1,fh);
		fread(&Timestamp,8,1,fh);
		fread(&Npoints,4,1,fh);
		while(Npoints>0)
		{
			rdcnt = fread(buffer, 1, BUF_SIZE, fh);
			current_pos = ftell(fh);
			fwrite(buffer, 1, rdcnt, fh_w);
			Npoints-=rdcnt;
		}
	}
	fclose(fh);
	fclose(fh_w);
	return 0;
}