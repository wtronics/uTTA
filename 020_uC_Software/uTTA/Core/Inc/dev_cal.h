/*
 * dev_cal.h
 *
 *  Created on: Oct 15, 2024
 *      Author: wtronics
 */

#ifndef INC_DEV_CAL_H_
#define INC_DEV_CAL_H_

#include "lfs.h"


#ifdef __cplusplus
extern "C" {
#endif

#define MaxCalChannels 16

typedef struct ChannelCalibration{
	float Offset;
	float LinGain;
	float CubGain;
} CH_Cal;

extern CH_Cal ChannelCalibValues[MaxCalChannels];
extern int8_t CalAvailable;

// {"DIFF0", "DIFF1", "DIFF2", "DIFF3", "ADC_I", "PA_00", "PA_01", "PA_02", "PA_03", "PA_10", "PA_20", "DAC_ISEN", "DAC_SPARE", "DAC_OFF0", "DAC_OFF1"};

typedef enum AnalogChannels{
	DIFF_Ch0,	// Differential Amplifer of the driven (heated JUT)
	DIFF_Ch1,	// Differential Amplifer  of the first monitor JUT
	DIFF_Ch2,	// Differential Amplifer  of the second monitor JUT
	DIFF_Ch3,	// Differential Amplifer  of the third monitor JUT (Spare)
	ADC_ChI,	// Current Measurement scaling
	PA_00,		// Cal Values for post amplifier settings 0-3 of channel 0
	PA_01,
	PA_02,
	PA_03,
	PA_10,		// Cal Values for post amplifier of channel 1
	PA_20,		// Cal Values for post amplifier of channel 2
	PA_30,		// Cal Values for post amplifier of channel 3, SPARE for not populated channel
	DAC_Ch_ISEN,	// Sense Current calibration
	DAC_CH_VOffs0,	// Offset Voltage calibration of the heated channel
	DAC_Ch_VOffs1_3,	// Offset Voltage calibration of all monitor channels
	CH_Last				// This is not a channel, this is just to get the length of the enum
}AnalogCh_t;


extern const char *CalChannelNames[];



void Write_CalibrationToFlash(lfs_t *lfs, lfs_file_t *file);
void Read_CalibrationFromFlash(lfs_t *lfs, lfs_file_t *file, uint8_t details);
int Write_CalibrationToFile(lfs_t *lfs, lfs_file_t *file);

int8_t WriteFileHeaderToFile(lfs_t *lfs, lfs_file_t *file);
int8_t WriteFileFooterToFile(lfs_t *lfs, lfs_file_t *file, int32_t CoolingStartBlock, int32_t TotalBlocks);


#ifdef __cplusplus
}
#endif

#endif /* INC_DEV_CAL_H_ */
