/*
 * dev_cal.c
 *
 *  Created on: Oct 15, 2024
 *      Author: wtronics
 */

#include "dev_cal.h"
#include "config_parameters.h"


CH_Cal ChannelCalibValues[MaxCalChannels];
int8_t CalAvailable = -1;		// -1 No Calibration available, 1 = Calibration available
const char *CalChannelNames[] = {"DIFF0", "DIFF1", "DIFF2", "DIFF3", "ADC_I", "PA_00", "PA_01", "PA_02", "PA_03", "PA_10", "PA_20","PA_30", "DAC_ISEN", "DAC_SPARE", "DAC_OFF0", "DAC_OFF1"};

extern char LogWriteBfr[TX_BFR_SIZE];
extern volatile Timing_t SamplingTiming;

/**
  * @brief Write the whole calibration data array to the flash memory in the the "Cali.ucf"-file
    @param  lfs_t *	      lfs			Pointer to the littlefs file system struct
    @param  lfs_file_t *  file			Pointer to the littlefs file struct
    @returns none
*/
/**************************************************************************/
void Write_CalibrationToFlash(lfs_t *lfs, lfs_file_t *file){

	int LFS_ret = 0;

	// Open the file and check if it is really available
	LFS_ret = lfs_file_open(lfs, file, "Cali.ucf", LFS_O_WRONLY | LFS_O_CREAT | LFS_O_TRUNC);
	if( LFS_ret < 0){
		ErrorResponse(ERRC_SYSTEM_ERROR, ERST_FILE_NOT_FOUND);
		return;
	}

	UART_printf("Writing calibration\n");

	// Write the data to the file
	LFS_ret = lfs_file_write(lfs, file, &ChannelCalibValues, sizeof(ChannelCalibValues));

	/* Close file */
	LFS_ret = lfs_file_close(lfs, file);

	if( LFS_ret < 0){
		ErrorResponse(ERRC_FILE_SYSTEM, (uint8_t)LFS_ret);
		return;
	}
}


/**
  * @brief Read the whole calibration data array from the flash memory into the uC memory
    @param  lfs_t *	      lfs			Pointer to the littlefs file system struct
    @param  lfs_file_t *  file			Pointer to the littlefs file struct
    @returns none
*/
/**************************************************************************/
void Read_CalibrationFromFlash(lfs_t *lfs, lfs_file_t *file){

	int LFS_ret = 0;
	UART_printf("CALIBRATION_FILE:\n");

	// Open the file and check if it is really available
	LFS_ret = lfs_file_open(lfs, file, "Cali.ucf", LFS_O_RDONLY);
	if( LFS_ret < 0){
		UART_printf("NO_FILE\n");
		//ErrorResponse(ERRC_SYSTEM_ERROR, ERST_FILE_NOT_FOUND);
		CalAvailable = -1;
		return;
	}

	// read the file from the memory in one step
	LFS_ret = lfs_file_read(lfs, file, &ChannelCalibValues, sizeof(ChannelCalibValues));
	/* Close file */
	LFS_ret = lfs_file_close(lfs, file);

	if( LFS_ret < 0){
		ErrorResponse(ERRC_FILE_SYSTEM, (uint8_t)LFS_ret);
		return;
	}
	CalAvailable = 1;

	for(uint8_t ValIdx = 0; ValIdx < MaxCalChannels; ValIdx++){
		UART_printf("%s,%f,%f,%f\n",CalChannelNames[ValIdx], ChannelCalibValues[ValIdx].Offset, ChannelCalibValues[ValIdx].LinGain, ChannelCalibValues[ValIdx].CubGain);
	}
}

/**
  * @brief Write the calibration values from memory to a currently open measurement file into the file header
    @param  lfs_t *	      lfs			Pointer to the littlefs file system struct
    @param  lfs_file_t *  file			Pointer to the littlefs file struct
    @returns none
*/
/**************************************************************************/
int Write_CalibrationToFile(lfs_t *lfs, lfs_file_t *file){
	int LFS_ret = 0;
	char FileWriteBuff[65];

	if(CalAvailable > 0){
		for(uint8_t ValIdx = 0; ValIdx < MaxCalChannels; ValIdx++){
			sprintf(FileWriteBuff,"#CAL_%s;%f;%f;%f\n",CalChannelNames[ValIdx], ChannelCalibValues[ValIdx].Offset, ChannelCalibValues[ValIdx].LinGain, ChannelCalibValues[ValIdx].CubGain);
			LFS_WRITE_STRING(lfs, file, FileWriteBuff);
		}
	}else{
		for(uint8_t ValIdx = 0; ValIdx < MaxCalChannels; ValIdx++){
			sprintf(FileWriteBuff,"#CAL_%s;-1.0;-1.0;-1.0\n",CalChannelNames[ValIdx]);
			LFS_WRITE_STRING(lfs, file, FileWriteBuff);
		}
	}

	sprintf(FileWriteBuff,"#ISEN;%f\n",DAC_SetVal[CH_ISEN]);
	LFS_WRITE_STRING(lfs, file, FileWriteBuff);

	sprintf(FileWriteBuff,"#VOFFS0;%f\n",DAC_SetVal[CH_VOffs0]);
	LFS_WRITE_STRING(lfs, file, FileWriteBuff);

	sprintf(FileWriteBuff,"#VOFFS1;%f\n",DAC_SetVal[CH_VOffs1_3]);
	LFS_WRITE_STRING(lfs, file, FileWriteBuff);


	return LFS_ret;
}


/**************************************************************************/
/*!
    @brief  Writes the file header with all information to the file
    @param none
    @returns none
*/
/**************************************************************************/
int8_t WriteFileHeaderToFile(lfs_t *lfs, lfs_file_t *file){
	int8_t LFS_ret=0;
	/* Writing text */
	RTC_TimeTypeDef Time;
	RTC_DateTypeDef Date;
	RTC_read_date(&Date);
	RTC_read_time(&Time);
	sprintf(LogWriteBfr,"FileVersion;" T3R_FILEVERSION "\n");
	EvalLFSError(LFS_WRITE_STRING(lfs, file, LogWriteBfr));

	Write_CalibrationToFile(lfs, file);

	sprintf(LogWriteBfr,"CH1 Name;%s;%f;%f;%f\n",Channels[0].CH_Name,Channels[0].CH_Offs,Channels[0].CH_LinGain,Channels[0].CH_QuadGain);
	EvalLFSError(LFS_WRITE_STRING(lfs, file, LogWriteBfr));

	sprintf(LogWriteBfr,"CH2 Name;%s;%f;%f;%f\n",Channels[1].CH_Name,Channels[1].CH_Offs,Channels[1].CH_LinGain,Channels[1].CH_QuadGain);
	EvalLFSError(LFS_WRITE_STRING(lfs, file, LogWriteBfr));

	sprintf(LogWriteBfr,"CH3 Name;%s;%f;%f;%f\n",Channels[2].CH_Name,Channels[2].CH_Offs,Channels[2].CH_LinGain,Channels[2].CH_QuadGain);
	EvalLFSError(LFS_WRITE_STRING(lfs, file, LogWriteBfr));

	sprintf(LogWriteBfr,"StartTime;%02d:%02d:%02d\n",Time.RTC_Hours,Time.RTC_Minutes,Time.RTC_Seconds);
	EvalLFSError(LFS_WRITE_STRING(lfs, file, LogWriteBfr));

	sprintf(LogWriteBfr,"StartDate;%02d.%02d.%04d\n",Date.RTC_Date, Date.RTC_Month, ((uint16_t)Date.RTC_Year)+2000);
	EvalLFSError(LFS_WRITE_STRING(lfs, file, LogWriteBfr));

	//sprintf(LogWriteBfr,"Tsamp,fast;%lu\n",SamplingTiming.FastSampleTime);
	//EvalLFSError(LFS_WRITE_STRING(lfs, file, LogWriteBfr));

	//sprintf(LogWriteBfr,"Tsamp,low;%lu\n",SamplingTiming.FastSampleTime<<SamplingTiming.MaxTimeMultiplier);
	//EvalLFSError(LFS_WRITE_STRING(lfs, file, LogWriteBfr));

	sprintf(LogWriteBfr,"Samples/Decade;%u\n",ADC_BFR_SIZE);
	EvalLFSError(LFS_WRITE_STRING(lfs, file, LogWriteBfr));

	//sprintf(LogWriteBfr,"Max. Divider;%lu\n",SamplingTiming.MaxTimeMultiplier);
	//EvalLFSError(LFS_WRITE_STRING(lfs, file, LogWriteBfr));

	sprintf(LogWriteBfr,"T_Preheat;%lu\n",SamplingTiming.PreHeatingTime/1000);
	EvalLFSError(LFS_WRITE_STRING(lfs, file, LogWriteBfr));

	sprintf(LogWriteBfr,"T_Heat;%lu\n",SamplingTiming.HeatingTime/1000);
	EvalLFSError(LFS_WRITE_STRING(lfs, file, LogWriteBfr));

	sprintf(LogWriteBfr,"T_Cool;%lu\n",SamplingTiming.CoolingTime/1000);
	EvalLFSError(LFS_WRITE_STRING(lfs, file, LogWriteBfr));

	EvalLFSError(LFS_WRITE_STRING(lfs, file, "ADC1;ADC2;ADC3;ADC4\n"));

	return LFS_ret;
}


/**************************************************************************/
/*!
    @brief  Writes the file header with all information to the file
    @param none
    @returns none
*/
/**************************************************************************/
int8_t WriteFileFooterToFile(lfs_t *lfs, lfs_file_t *file, int32_t CoolingStartBlock, int32_t TotalBlocks){
	RTC_TimeTypeDef Time;
	int8_t LFS_ret = 0;

	sprintf(LogWriteBfr,"Cooling Start Block;%lu\nTotal Blocks;%lu\n", CoolingStartBlock, TotalBlocks);
	EvalLFSError(LFS_WRITE_STRING(lfs, file, LogWriteBfr));

	RTC_read_time(&Time);

	sprintf(LogWriteBfr,"Finished;%02u:%02u:%02u\nEnd of Log", Time.RTC_Hours,Time.RTC_Minutes,Time.RTC_Seconds);
	EvalLFSError(LFS_WRITE_STRING(lfs, file, LogWriteBfr));
	return LFS_ret;
}




