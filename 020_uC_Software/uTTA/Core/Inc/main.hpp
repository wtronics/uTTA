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


#include "stm32f3xx_it.h"
#include "math.h"

/* Private includes ----------------------------------------------------------*/
#include <stdio.h>
#include <ctype.h>
#include <string.h>

#include "config_parameters.h"
#include "gpio_definition.h"
#include "build_defs.h"

#include "spi_func.h"
#include "gpio_func.h"
#include "dma_func.h"
#include "tim_func.h"
#include "adc_func.h"
#include "uart_func.h"

#include "ErrorCodes.h"
#include "rtc.h"
#include "w25qxx_littlefs.h"
#include "lfs.h"
#include "ad56x4.h"


/* Exported functions prototypes ---------------------------------------------*/
void Error_Handler(void);
void DoMeasurement(void);
uint8_t WriteBlockToFile(uint8_t ReadBlock, uint32_t TotalWrittenBlocks);

uint8_t WriteTemperaturesToFile(void);
void SampleClockHandler(void);


/* Private defines -----------------------------------------------------------*/

//#define DEBUG_INIT

#ifdef DEBUG_INIT
#define INIT_DBG(...) UART_printf(__VA_ARGS__)
#else
#define INIT_DBG(...)
#endif

union ADC_conv{
  uint32_t ADC_Reg;
  uint16_t ADC_Val[2];
};


#ifdef __cplusplus
}
#endif

#endif /* __MAIN_H */
