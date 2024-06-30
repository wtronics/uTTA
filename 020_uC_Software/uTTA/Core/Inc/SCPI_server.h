/*
 * SCPI_server.h
 *
 *  Created on: Jun 29, 2022
 *      Author: wtronics
 */

#ifndef INC_SCPI_SERVER_H_
#define INC_SCPI_SERVER_H_

//#include "stm32f3xx_hal.h"

//#include "fatfs.h"
#include <stdio.h>
#include <string.h>
#include "stm32f3xx_ll_usart.h"
#include "Vrekrer_scpi_parser.hpp"


#ifdef __cplusplus
extern "C" {
#endif

#include "uart_func.h"
#include "ErrorCodes.h"
#include "rtc.h"
#include "main.h"

//SCPI Function Prototypes
void Init_SCPI_server(void);
void SystemReset(SCPI_C commands, SCPI_P parameters, USART_TypeDef *huart);
void Identify(SCPI_C commands, SCPI_P parameters, USART_TypeDef *huart);			// returns the device identification string
void SystemErrorStatus(SCPI_C commands, SCPI_P parameters, USART_TypeDef *huart);
void SystemStatus(SCPI_C commands, SCPI_P parameters, USART_TypeDef *huart);

void SetPSUEnable(SCPI_C commands, SCPI_P parameters, USART_TypeDef *huart);		// switches the power supply enable output
void GetPSUEnable(SCPI_C commands, SCPI_P parameters, USART_TypeDef *huart);		// read the status of the power supply enable output
void SetPWSTGEnable(SCPI_C commands, SCPI_P parameters, USART_TypeDef *huart);		// switches the measurement power stage output
void GetPWSTGEnable(SCPI_C commands, SCPI_P parameters, USART_TypeDef *huart);		// read the status of the power stage enable output
void SetGD_PowerEnable(SCPI_C commands, SCPI_P parameters, USART_TypeDef *huart);		// enables the gatedriver supply of the power stage output
void GetGD_PowerEnable(SCPI_C commands, SCPI_P parameters, USART_TypeDef *huart);		// read the status of the gatedriver supply of the power stage output
void GetPWSTGUVLO(SCPI_C commands, SCPI_P parameters, USART_TypeDef *huart);		// read the status of the power stage undervoltage lockout pin
void Read_Memory_File(SCPI_C commands, SCPI_P parameters, USART_TypeDef *huart);		// reads a file from the SD-Card and prints it on the serial interface
void Delete_Memory_File(SCPI_C commands, SCPI_P parameters, USART_TypeDef *huart);		// deletes a file from the SD-Card
void Write_Memory_Testfile(SCPI_C commands, SCPI_P parameters, USART_TypeDef *huart);	// performs a SD write speed test
void Read_Memory_Directory(SCPI_C commands, SCPI_P parameters, USART_TypeDef *huart);
void SetSampling(SCPI_C commands, SCPI_P parameters, USART_TypeDef *huart);		// Sets the samplerate for all States
void GetSampling(SCPI_C commands, SCPI_P parameters, USART_TypeDef *huart);		//
void SetTiming(SCPI_C commands, SCPI_P parameters, USART_TypeDef *huart);			// All time parameters for all Measurement steps
void GetTiming(SCPI_C commands, SCPI_P parameters, USART_TypeDef *huart);			//
void SetMeasure(SCPI_C commands, SCPI_P parameters, USART_TypeDef *huart);			// Start and Stop the measurement
void SetMode(SCPI_C commands, SCPI_P parameters, USART_TypeDef *huart);
void SetChannelDescription(SCPI_C commands, SCPI_P parameters, USART_TypeDef *huart);
void SetCalSampleRate(SCPI_C commands, SCPI_P parameters, USART_TypeDef *huart);
void SetDUT(SCPI_C commands, SCPI_P parameters, USART_TypeDef *huart);
void SetGain(SCPI_C commands, SCPI_P parameters, USART_TypeDef *huart);
void GetGain(SCPI_C commands, SCPI_P parameters, USART_TypeDef *huart);
void GetSystemTime(SCPI_C commands, SCPI_P parameters, USART_TypeDef *huart);
void SetSystemTime(SCPI_C commands, SCPI_P parameters, USART_TypeDef *huart);

void SetPGAGain(uint8_t Gain);
void GetSamplingSettings(void);

int lfs_ls(lfs_t *lfs, const char *path) ;


typedef struct PGA_Gain_{
	uint8_t Set=PGA_DEF_GAIN;
	uint8_t Cooling;
	uint8_t Heating;
} PGA;

typedef struct Sampling_Timing_{
	uint32_t FastSampleTime    = ADC_DEF_SAMPLETIME;
	float    FastSampleRate	   = 0.0f;
	uint32_t MaxTimeMultiplier = ADC_MAX_MULTIPLIER;
	uint32_t SetSampleTime     = ADC_MAX_SAMPLERATE << ADC_MAX_MULTIPLIER;
	uint32_t SetMultiplier     = ADC_MAX_MULTIPLIER;
	uint32_t PreHeatingTime    = MEAS_DEF_PREHEATING_TIME;
	uint32_t HeatingTime       = MEAS_DEF_HEATING_TIME;
	uint32_t CoolingTime       = MEAS_DEF_COOLING_TIME;
	uint32_t CalSampleTime     = CAL_DEF_SAMPLE_TIME;
} Timing;

//typedef enum FileScanOptions_t{
//	FSO_NoDetail = 0,
//	FSO_EditTime
//}FSO_t;

extern lfs_file_t file;
extern lfs_t littlefs;

extern uint8_t ErrorTotalCount;


#ifdef __cplusplus
}
#endif


#endif /* INC_SCPI_SERVER_H_ */
