/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file    rtc.h
  * @brief   This file contains all the function prototypes for
  *          the rtc.c file
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2022 STMicroelectronics.
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
#ifndef __RTC_H__
#define __RTC_H__

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ------------------------------------------------------------------*/
#include "main.h"
#include <stdio.h>
#include <string.h>
#include <time.h>
#include "uart_func.h"

// RTC time structure
typedef struct {
	uint8_t RTC_Hours;   // RTC time hour, the value range is [0..23] or [0..12] depending of hour format
	uint8_t RTC_Minutes; // RTC time minutes, the value range is [0..59]
	uint8_t RTC_Seconds; // RTC time minutes, the value range is [0..59]
	uint8_t RTC_H12;     // RTC AM/PM time
} RTC_TimeTypeDef;

// RTC date structure
typedef struct {
	uint8_t RTC_WeekDay; // RTC date week day (one of RTC_DOW_XXX definitions)
	uint8_t RTC_Month;   // RTC date month (in BCD format, one of RTC_MONTH_XXX definitions)
	uint8_t RTC_Date;    // RTC date, the value range is [1..31]
	uint8_t RTC_Year;    // RTC date year, the value range is [0..99]
} RTC_DateTypeDef;

void MX_RTC_Init(void);							// RTC init function
void RTC_read_time(RTC_TimeTypeDef *time);		// reads the time from the RTC
void RTC_read_date(RTC_DateTypeDef *date);		// reads the date from the RTC
void RTC_write_date_fmt(uint16_t year, uint8_t month, uint8_t day, uint8_t weekday);	// Set the date of the RTC
void RTC_write_time_fmt(uint8_t hour, uint8_t minute, uint8_t second);					// Set the time of the RTC
void RTC_write_time_struct(RTC_TimeTypeDef* Time);
void RTC_write_date_struct(RTC_DateTypeDef* Date);
void RTC_write_time(uint8_t ht, uint8_t hu, uint8_t mnt, uint8_t mnu, uint8_t st, uint8_t su);		// Write digits to the RTC time register in 24h format.
void RTC_write_date(uint8_t yt, uint8_t yu, uint8_t mt, uint8_t mu, uint8_t dt, uint8_t du, uint8_t wdu);		// Write digits to the RTC date register.

void print_RTC_DateTime(RTC_DateTypeDef* Date ,RTC_TimeTypeDef* Time);
void print_RTC_Time(RTC_TimeTypeDef* Time);



#ifdef __cplusplus
}
#endif

#endif /* __RTC_H__ */

