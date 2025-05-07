/*
 * config_parameters.h
 *
 *  Created on: Oct 14, 2024
 *      Author: wtronics
 */

#ifndef INC_CONFIG_PARAMETERS_H_
#define INC_CONFIG_PARAMETERS_H_

/* Includes ------------------------------------------------------------------*/
#include "stm32f3xx_ll_adc.h"
#include "stm32f3xx_ll_dma.h"
#include "stm32f3xx_ll_rcc.h"
#include "stm32f3xx_ll_bus.h"
#include "stm32f3xx_ll_system.h"
#include "stm32f3xx_ll_exti.h"
#include "stm32f3xx_ll_cortex.h"
#include "stm32f3xx_ll_utils.h"
#include "stm32f3xx_ll_pwr.h"
#include "stm32f3xx_ll_spi.h"
#include "stm32f3xx_ll_tim.h"
#include "stm32f3xx_ll_usart.h"
#include "stm32f3xx_ll_gpio.h"
#include "stm32f3xx_ll_utils.h"

#include "stm32f3xx_it.h"

#if defined(USE_FULL_ASSERT)
#include "stm32_assert.h"
#endif /* USE_FULL_ASSERT */

#include "math.h"


#define UTTA_OWNER "WK"
#define UTTA_SERIAL_NO "001"

// Handle Definition for Flash-SPI and UART
#define SD_SPI_HANDLE 		SPI3
#define UART_HANDLE 		USART2
#define ADC_TIMER_HANDLE  	TIM3
#define ADC_MASTER_HANDLE	ADC1


// ADC Buffer definition
#define ADC_BFR_BLOCKS 20
#define ADC_BFR_SIZE   250

#define ADC1_DIODE1_PGA_IN_AI_CH 14
#define ADC2_DIODE2_IN_AI_CH     12
#define ADC3_DIODE2_IN_AI_CH     1
#define ADC4_DIODE2_IN_AI_CH     5
#define ADC4_CURRENT_IN_AI_CH    4



#define PRESC_SAMPLECLOCK_INITIAL 8000000UL
#define ADC_MAX_SAMPLERATE        2000000UL
#define ADC_MIN_SAMPLERATE         100000UL

#define SAMPLECLOCK_MASTER_FREQ 72000000UL
#define PRESCALER_UPSCALE_INITIAL SAMPLECLOCK_MASTER_FREQ/PRESC_SAMPLECLOCK_INITIAL

#define ADC_MAX_MULTIPLIER  17UL
#define ADC_DEF_SAMPLETIME	PRESC_SAMPLECLOCK_INITIAL/ADC_MAX_SAMPLERATE


#define MAX_DUT_NAME_LENGTH 18


#define MEASURE_DATA_UPDATE_TIME	500UL
#define MEASURE_TEMP_UPDATE_TIME	300UL

#ifdef DEBUG_SHORT_TIMES
	#define MEAS_DEF_PREHEATING_TIME	6000UL
	#define MEAS_DEF_HEATING_TIME		10000UL
	#define MEAS_DEF_COOLING_TIME		36000UL
#else
	#define MEAS_DEF_PREHEATING_TIME	60000UL
	#define MEAS_DEF_HEATING_TIME		2400000UL
	#define MEAS_DEF_COOLING_TIME		3600000UL
#endif

#define MEAS_MIN_PREHEATING_TIME   	30000UL		// 30 seconds
#define MEAS_MAX_PREHEATING_TIME   	21600000UL	// 6 hours	--> extended max preheating time to do calibration of TSP

#define MEAS_MIN_HEATING_TIME      	60000UL		// 60 seconds --> to skip heating and cooling phase you can also set the value to 0
#define MEAS_MAX_HEATING_TIME      	10800000UL	// 3 hours

#define MEAS_MIN_COOLING_TIME      	60000UL		// 60 seconds
#define MEAS_MAX_COOLING_TIME      	21600000UL	// 6 hours

#define TEST_DEF_SAMPLE_TIME		250UL
#define TEST_MAX_SAMPLE_TIME		2500UL
#define TEST_MIN_SAMPLE_TIME		25UL

#define PGA_DEF_GAIN				1
#define PGA_MIN_GAIN				0
#define PGA_MAX_GAIN				3

// DAC Default values when in calibrated state
#define ISEN_DEF_VALUE_mA        5.0f
#define VOFFS0_DEF_VALUE_V	    -0.2f
#define VOFFS1_3_DEF_VALUE_V	-0.3f

// DAC Default values when in non-calibrated state
#define ISEN_DEF_VALUE_RAW        32768.0f	// roughly 5.6mA
#define VOFFS0_DEF_VALUE_RAW	  18000.0f	// roughly -0.2V
#define VOFFS1_3_DEF_VALUE_RAW	  18000.0f	// roughly -0.2V

#define UTTA_SW_VERSION "2.4"
#define UMF_FILEVERSION "3.4"


//#define MODE_NORMAL      0
//#define MODE_TESTMODE    1
//#define MODE_TEMPCONTROL 2

typedef enum {
	 Mode_Normal,
	 Mode_Test,
	 Mode_TempControl
} DeviceModes_t;

typedef struct PGA_Gain_{
	uint8_t Set;
	uint8_t Cooling;
	uint8_t Heating;
} PGA_t;

typedef struct Sampling_Timing_{
	uint32_t FastSampleTime;
	float    FastSampleRate;
	uint32_t MaxTimeMultiplier;
	uint32_t SetSampleTime;
	uint32_t SetMultiplier;
	uint32_t PreHeatingTime;
	uint32_t HeatingTime;
	uint32_t CoolingTime;
	uint32_t TestSampleTime;
} Timing_t;


typedef enum {
	Meas_State_Idle = 0,		// 0 :  Measurement system is not active
	Meas_State_Init,			// 1 :
	Meas_State_GDPowerCheck,
	Meas_State_Preheating,
	Meas_State_PrepHeating,
	Meas_State_Heating,
	Meas_State_PrepCooling,
	Meas_State_Cooling,
	Meas_State_Deinit,
	Meas_State_CloseLog,
	Test_State_Init,
	Test_State_GDPowerOn,
	Test_State_GPPowerCheck,
	Test_State_Cal,
	Test_State_DeInit,
	Test_State_Exit,
	Temp_State_Init,
	Temp_State_Heat,
	Temp_State_Settle,
	Temp_State_Measure,
	Temp_State_Deinit,
}MeasurementStates_t;

typedef struct ChannelParams{
	char CH_Name[16];
	float CH_Offs;
	float CH_LinGain;
	float CH_QuadGain;
	uint8_t CalStatus;
} CH_Def;

extern DeviceModes_t OperatingMode;

extern CH_Def Channels[4];

extern char DUT_Name[MAX_DUT_NAME_LENGTH];

extern volatile MeasurementStates_t FlagMeasurementState;

#define LFS_WRITE_STRING(LittleFS,File,str)  lfs_file_write(LittleFS, File, str, strlen(str))


#endif /* INC_CONFIG_PARAMETERS_H_ */
