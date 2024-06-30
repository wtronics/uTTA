/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.h
  * @brief          : Header for main.c file.
  *                   This file contains the common defines of the application.
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2024 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* USER CODE END Header */

/* Define to prevent recursive inclusion -------------------------------------*/
#ifndef __MAIN_H
#define __MAIN_H

#ifdef __cplusplus
extern "C" {
#endif

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

#if defined(USE_FULL_ASSERT)
#include "stm32_assert.h"
#endif /* USE_FULL_ASSERT */

#include "math.h"

/* Private includes ----------------------------------------------------------*/

#include "uart_func.h"
#include "spi_func.h"
#include "gpio_func.h"
#include "dma_func.h"
#include "tim_func.h"
#include "adc_func.h"
#include "lfs.h"
#include "w25qxx_littlefs.h"
#include "stm32f3xx_it.h"


/* Exported functions prototypes ---------------------------------------------*/
void Error_Handler(void);

void DoMeasurement(void);
uint8_t MeasurementMemoryPrediction(void);
uint8_t WriteBlockToFile(uint8_t ReadBlock, uint32_t TotalWrittenBlocks);
int8_t WriteFileHeaderToFile(void);
int8_t WriteFileFooterToFile(void);
uint8_t WriteTemperaturesToFile(void);
void SampleClockHandler(void);


/* Private defines -----------------------------------------------------------*/
//Button 1 port
#define B1_Pin LL_GPIO_PIN_13
#define B1_GPIO_Port GPIOC
// On Board LED
#define LD2_Pin LL_GPIO_PIN_5
#define LD2_GPIO_Port GPIOA


// Debug IO1 port
#define DBG_IO1_Pin LL_GPIO_PIN_0
#define DBG_IO1_GPIO_Port GPIOC
// Debug IO2 port
#define DBG_IO2_Pin LL_GPIO_PIN_1
#define DBG_IO2_GPIO_Port GPIOC
// Debug IO3 port
#define DBG_IO3_Pin LL_GPIO_PIN_2
#define DBG_IO3_GPIO_Port GPIOC
// Debug IO4 port
#define DBG_IO4_Pin LL_GPIO_PIN_3
#define DBG_IO4_GPIO_Port GPIOC
// Debug Pin for Sample time generation timer
#define TIM_DBG_PO_Pin LL_GPIO_PIN_10
#define TIM_DBG_PO_GPIO_Port GPIOA


// Enable Powerstage pin
#define PWSTG_EN_DO_Pin LL_GPIO_PIN_0
#define PWSTG_EN_DO_GPIO_Port GPIOA
// Readback pin of powerstage power supply low
#define PWSTG_UVLO_DI_Pin LL_GPIO_PIN_1
#define PWSTG_UVLO_DI_GPIO_Port GPIOA
// Enable pin of external power supply
#define PSU_EN_DO_Pin LL_GPIO_PIN_4
#define PSU_EN_DO_GPIO_Port GPIOA
// Gate driver power supply enable
#define PWSTG_PWR_EN_DO_Pin LL_GPIO_PIN_0
#define PWSTG_PWR_EN_DO_GPIO_Port GPIOB


// Amplifier Gain Switching outputs
#define GAIN_B0_DO_Pin LL_GPIO_PIN_6
#define GAIN_B0_DO_GPIO_Port GPIOA
#define GAIN_B1_DO_Pin LL_GPIO_PIN_7
#define GAIN_B1_DO_GPIO_Port GPIOA


// Analog inputs for measurement
#define PGA_DIODE3_AI_Pin LL_GPIO_PIN_1
#define PGA_DIODE3_AI_GPIO_Port GPIOB
#define PGA_DIODE2_AI_Pin LL_GPIO_PIN_2
#define PGA_DIODE2_AI_GPIO_Port GPIOB
#define PGA_DIODE1_AI_Pin LL_GPIO_PIN_11
#define PGA_DIODE1_AI_GPIO_Port GPIOB
#define CURR_MEAS_AI_Pin LL_GPIO_PIN_14
#define CURR_MEAS_AI_GPIO_Port GPIOB
#define PGA_DIODE4_AI_Pin LL_GPIO_PIN_15
#define PGA_DIODE4_AI_GPIO_Port GPIOB


// SD card detection
#define SD_SPI_SCK_Pin LL_GPIO_PIN_10
#define SD_SPI_SCK_GPIO_Port GPIOC
#define SD_SPI_MISO_Pin LL_GPIO_PIN_11
#define SD_SPI_MISO_GPIO_Port GPIOC
#define SD_SPI_MOSI_Pin LL_GPIO_PIN_12
#define SD_SPI_MOSI_GPIO_Port GPIOC
#define SD_SPI_CS_Pin LL_GPIO_PIN_2
#define SD_SPI_CS_GPIO_Port GPIOD


// Type K temperature sensor chip select lines
#define TEMP_SPI_CSN0_Pin LL_GPIO_PIN_5
#define TEMP_SPI_CSN0_GPIO_Port GPIOC
#define TEMP_SPI_CSN1_Pin LL_GPIO_PIN_6
#define TEMP_SPI_CSN1_GPIO_Port GPIOC
#define TEMP_SPI_CSN2_Pin LL_GPIO_PIN_8
#define TEMP_SPI_CSN2_GPIO_Port GPIOC
#define TEMP_SPI_CSN3_Pin LL_GPIO_PIN_9
#define TEMP_SPI_CSN3_GPIO_Port GPIOC
// Type K Sensor SCK Line
#define TEMP_SPI_SCK_Pin LL_GPIO_PIN_8
#define TEMP_SPI_SCK_GPIO_Port GPIOB
// Type K Sensor MISO Line
#define TEMP_SPI_MISO_Pin LL_GPIO_PIN_9
#define TEMP_SPI_MISO_GPIO_Port GPIOB


// USART RX/TX pins
#define USART_TX_Pin LL_GPIO_PIN_2
#define USART_TX_GPIO_Port GPIOA
#define USART_RX_Pin LL_GPIO_PIN_3
#define USART_RX_GPIO_Port GPIOA


// NOT USED USB Interface detection
#define USB_DEV_DETECT_DO_Pin LL_GPIO_PIN_9
#define USB_DEV_DETECT_DO_GPIO_Port GPIOA


// External debugger connection
#define TMS_Pin LL_GPIO_PIN_13
#define TMS_GPIO_Port GPIOA
#define TCK_Pin LL_GPIO_PIN_14
#define TCK_GPIO_Port GPIOA
#define SWO_Pin LL_GPIO_PIN_3
#define SWO_GPIO_Port GPIOB


#ifndef NVIC_PRIORITYGROUP_0
#define NVIC_PRIORITYGROUP_0         ((uint32_t)0x00000007) /*!< 0 bit  for pre-emption priority,
                                                                 4 bits for subpriority */
#define NVIC_PRIORITYGROUP_1         ((uint32_t)0x00000006) /*!< 1 bit  for pre-emption priority,
                                                                 3 bits for subpriority */
#define NVIC_PRIORITYGROUP_2         ((uint32_t)0x00000005) /*!< 2 bits for pre-emption priority,
                                                                 2 bits for subpriority */
#define NVIC_PRIORITYGROUP_3         ((uint32_t)0x00000004) /*!< 3 bits for pre-emption priority,
                                                                 1 bit  for subpriority */
#define NVIC_PRIORITYGROUP_4         ((uint32_t)0x00000003) /*!< 4 bits for pre-emption priority,
                                                                 0 bit  for subpriority */
#endif

/* USER CODE BEGIN Private defines */
// Handle Definition for SD-SPI and UART
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



#ifdef DEBUG_SLOW_ADC
	#define PRESC_SAMPLECLOCK_INITIAL 2000000UL
	#define ADC_MAX_SAMPLERATE  200000UL
    #define ADC_MIN_SAMPLERATE   50000UL
#else
	#define PRESC_SAMPLECLOCK_INITIAL 8000000UL
	#define ADC_MAX_SAMPLERATE        2000000UL
    #define ADC_MIN_SAMPLERATE         100000UL

#endif

#define SAMPLECLOCK_MASTER_FREQ 72000000UL
#define PRESCALER_UPSCALE_INITIAL SAMPLECLOCK_MASTER_FREQ/PRESC_SAMPLECLOCK_INITIAL


#define ADC_DEF_SAMPLETIME	PRESC_SAMPLECLOCK_INITIAL/ADC_MAX_SAMPLERATE
#define ADC_MAX_MULTIPLIER  17UL
#define ADC_MIN_DIVIDER      1UL

#define MAX_DUT_NAME_LENGTH 18

extern char DUT_Name[MAX_DUT_NAME_LENGTH];
typedef struct ChannelParams{
	char CH_Name[16];
	int32_t CH_Offs;
	int32_t CH_LinGain;
	int32_t CH_QuadGain;
} CH_Def;

extern CH_Def Channels[4];



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

#define MEAS_MIN_PREHEATING_TIME   	30000UL		//Milliseconds!
#define MEAS_MAX_PREHEATING_TIME   	3600000UL

#define MEAS_MIN_HEATING_TIME      	10000UL
#define MEAS_MAX_HEATING_TIME      	10800000UL

#define MEAS_MIN_COOLING_TIME      	60000UL
#define MEAS_MAX_COOLING_TIME      	21600000UL

#define CAL_DEF_SAMPLE_TIME			250UL
#define CAL_MAX_SAMPLE_TIME			2500UL
#define CAL_MIN_SAMPLE_TIME			25UL

#define PGA_DEF_GAIN				1
#define PGA_MIN_GAIN				0
#define PGA_MAX_GAIN				3


typedef enum {
	Meas_State_Idle = 0,		// 0 :  Measurement system is not active
	Meas_State_Init,			// 1 :
	//Meas_State_GDPowerOn,
	Meas_State_GDPowerCheck,
	Meas_State_Preheating,
	Meas_State_PrepHeating,
	Meas_State_Heating,
	Meas_State_PrepCooling,
	Meas_State_Cooling,
	Meas_State_Deinit,
	Meas_State_CloseLog,
	Cal_State_Init,
	Cal_State_GDPowerOn,
	Cal_State_GPPowerCheck,
	Cal_State_Cal,
	Cal_State_DeInit
}MeasurementStates_t;

extern volatile MeasurementStates_t FlagMeasurementState;


#define UTTA_SW_VERSION "1.0"
#define T3R_FILEVERSION "2.2"

extern uint8_t OperatingMode;
#define MODE_NORMAL      0
#define MODE_CALIBRATION 1

union ADC_conv{
  uint32_t ADC_Reg;
  uint16_t ADC_Val[2];
};


#define LFS_WRITE_STRING(LittleFS,File,str)  lfs_file_write(&LittleFS, &File, &str, strlen(str))


#ifdef __cplusplus
}
#endif

#endif /* __MAIN_H */
