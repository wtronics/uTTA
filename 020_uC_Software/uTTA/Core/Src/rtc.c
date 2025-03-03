/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file    rtc.c
  * @brief   This file provides code for the configuration
  *          of the RTC instances.
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
/* Includes ------------------------------------------------------------------*/
#include "rtc.h"



/* RTC init function */
void MX_RTC_Init(void)
{
    // Enable the power interface
	LL_APB1_GRP1_EnableClock(LL_APB1_GRP1_PERIPH_PWR);
    //SET_BIT(RCC->APB1ENR, RCC_APB1ENR_PWREN);

    // Enable access to the backup domain
    SET_BIT(PWR->CR, PWR_CR_DBP);

    // Enable LSE oscillator with medium driver power
    LL_RCC_LSE_SetDriveCapability(LL_RCC_LSEDRIVE_MEDIUMLOW);
    LL_RCC_LSE_Enable();


    // Wait until LSE oscillator is ready
    while(!LL_RCC_LSE_IsReady()) {}

    // Select LSE as clock source for the RTC
    LL_RCC_SetRTCClockSource(LL_RCC_RTC_CLKSOURCE_LSE);

    // Enable the RTC
    LL_RCC_EnableRTC();

}


/**************************************************************************/
/*!
    @brief  reads the time from the RTC
    @param  RTC_TimeTypeDef *time		Time structure pointer
    @returns none
*/
/**************************************************************************/
void RTC_read_time(RTC_TimeTypeDef *time)
{

	// Extract digits from the RTC time register
    uint8_t ht=  (RTC->TR & RTC_TR_HT)  >> RTC_TR_HT_Pos;
    uint8_t hu=  (RTC->TR & RTC_TR_HU)  >> RTC_TR_HU_Pos;
    uint8_t mnt= (RTC->TR & RTC_TR_MNT) >> RTC_TR_MNT_Pos;
    uint8_t mnu= (RTC->TR & RTC_TR_MNU) >> RTC_TR_MNU_Pos;
    uint8_t st=  (RTC->TR & RTC_TR_ST)  >> RTC_TR_ST_Pos;
    uint8_t su=  (RTC->TR & RTC_TR_SU)  >> RTC_TR_SU_Pos;

    time->RTC_Hours= ht*10+hu;
    time->RTC_Minutes=mnt*10+mnu;
    time->RTC_Seconds=st*10+su;
}



/**************************************************************************/
/*!
    @brief  reads the date from the RTC
    @param  RTC_DateTypeDef *date		Date structure pointer
    @returns none
*/
/**************************************************************************/
void RTC_read_date(RTC_DateTypeDef *date)
{
	// Extract digits from the RTC date register
	uint8_t yt= (RTC->DR & RTC_DR_YT) >> RTC_DR_YT_Pos;
	uint8_t yu= (RTC->DR & RTC_DR_YU) >> RTC_DR_YU_Pos;
	uint8_t mt= (RTC->DR & RTC_DR_MT) >> RTC_DR_MT_Pos;
	uint8_t mu= (RTC->DR & RTC_DR_MU) >> RTC_DR_MU_Pos;
	uint8_t dt= (RTC->DR & RTC_DR_DT) >> RTC_DR_DT_Pos;
	uint8_t du= (RTC->DR & RTC_DR_DU) >> RTC_DR_DU_Pos;

	date->RTC_Year = yt*10 + yu;
	date->RTC_Month = mt*10 + mu;
	date->RTC_Date = dt*10 + du;
	date->RTC_WeekDay = (RTC->DR & RTC_DR_WDU) >> RTC_DR_WDU_Pos;
}

/**************************************************************************/
/*!
    @brief  Set the date of the RTC
    @param  uint16_t year
    @param  uint8_t month
    @param  uint8_t day
    @param  uint8_t weekday
    @returns none
*/
/**************************************************************************/
void RTC_write_date_fmt(uint16_t year, uint8_t month, uint8_t day, uint8_t weekday){
	RTC_write_date((year/10)%10, year%10, month/10, month%10, day/10, day%10, weekday);
}

/**************************************************************************/
/*!
    @brief  Set the date of the RTC by using an RTC_DateTypeDef structure
    @param  RTC_DateTypeDef* Date
    @returns none
*/
/**************************************************************************/
void RTC_write_date_struct(RTC_DateTypeDef* Date){
	RTC_write_date((Date->RTC_Year/10), Date->RTC_Year%10, Date->RTC_Month/10, Date->RTC_Month%10, Date->RTC_Date/10, Date->RTC_Date%10, Date->RTC_WeekDay);
}

/**************************************************************************/
/*!
    @brief  Set the time of the RTC
    @param  uint8_t hour
    @param  uint8_t minute
    @param  uint8_t second
    @returns none
*/
/**************************************************************************/
void RTC_write_time_fmt(uint8_t hour, uint8_t minute, uint8_t second){
	RTC_write_time(hour/10,hour%10,minute/10,minute%10,second/10, second%10);
}


/**************************************************************************/
/*!
    @brief  Set the time of the day of the RTC by using an RTC_TimeTypeDef structure
    @param  RTC_TimeTypeDef* Date
    @returns none
*/
/**************************************************************************/
void RTC_write_time_struct(RTC_TimeTypeDef* Time){
	RTC_write_time(Time->RTC_Hours/10,Time->RTC_Hours%10,Time->RTC_Minutes/10,Time->RTC_Minutes%10,Time->RTC_Seconds/10, Time->RTC_Seconds%10);
}


/**
 * Write digits to the RTC time register in 24h format.
 * @param ht tens of hour
 * @param hu ones of hours
 * @param mnt tens of minutes
 * @param mnu ones of minutes
 * @param st tens of seconds
 * @param su ones of seconds
 */
void RTC_write_time(uint8_t ht, uint8_t hu, uint8_t mnt, uint8_t mnu, uint8_t st, uint8_t su)
{
    // Calculate the new value for the time register
    uint32_t tmp=READ_REG(RTC->TR);
    tmp &= ~(RTC_TR_HT+RTC_TR_HU+RTC_TR_MNT+RTC_TR_MNU+RTC_TR_ST+RTC_TR_SU+RTC_TR_PM); // Keep only the reserved bits
    tmp += (uint32_t) ht << RTC_TR_HT_Pos;
    tmp += (uint32_t) hu << RTC_TR_HU_Pos;
    tmp += (uint32_t) mnt << RTC_TR_MNT_Pos;
    tmp += (uint32_t) mnu << RTC_TR_MNU_Pos;
    tmp += (uint32_t) st << RTC_TR_ST_Pos;
    tmp += (uint32_t) su << RTC_TR_SU_Pos;

    // Unlock the write protection
    WRITE_REG(RTC->WPR, 0xCA);
    WRITE_REG(RTC->WPR, 0x53);

    // Enter initialization mode
    SET_BIT(RTC->ISR, RTC_ISR_INIT);

    // Wait until the initialization mode is active
    while (!READ_BIT(RTC->ISR, RTC_ISR_INITF)) {};

    // The 24h format is already the default
    // CLEAR_BIT(RTC->CR, RTC_CR_FMT);

    // Update the time register
    WRITE_REG(RTC->TR,tmp);

    // Leave the initialization mode
    CLEAR_BIT(RTC->ISR, RTC_ISR_INIT);

    // Trigger a synchronization of the shadow registers
    CLEAR_BIT(RTC->ISR, RTC_ISR_RSF);

    // Wait until the shadow registers are synchronized
    while (!READ_BIT(RTC->ISR, RTC_ISR_RSF)) {};

    // Switch the write protection back on
    WRITE_REG(RTC->WPR, 0xFF);
}

/**
 * Write digits to the RTC date register.
 * @param yt tens of year
 * @param yu ones of year
 * @param mt tens of month
 * @param mu ones of month
 * @param dt tens of day
 * @param du ones of day
 * @param wdu week day (1-7)
 */
void RTC_write_date(uint8_t yt, uint8_t yu, uint8_t mt, uint8_t mu, uint8_t dt, uint8_t du, uint8_t wdu)
{
    // Calculate the new value for the date register
    uint32_t tmp=READ_REG(RTC->DR);
    tmp &= ~(RTC_DR_YT+RTC_DR_YU+RTC_DR_MT+RTC_DR_MU+RTC_DR_DT+RTC_DR_DU+RTC_DR_WDU); // Keep only the reserved bits
    tmp += (uint32_t) yt << RTC_DR_YT_Pos;
    tmp += (uint32_t) yu << RTC_DR_YU_Pos;
    tmp += (uint32_t) mt << RTC_DR_MT_Pos;
    tmp += (uint32_t) mu << RTC_DR_MU_Pos;
    tmp += (uint32_t) dt << RTC_DR_DT_Pos;
    tmp += (uint32_t) du << RTC_DR_DU_Pos;
    tmp += (uint32_t) wdu << RTC_DR_WDU_Pos;

    // Unlock the write protection
    WRITE_REG(RTC->WPR, 0xCA);
    WRITE_REG(RTC->WPR, 0x53);

    // Enter initialization mode
    SET_BIT(RTC->ISR, RTC_ISR_INIT);

    // Wait until the initialization mode is active
    while (!READ_BIT(RTC->ISR, RTC_ISR_INITF)) {};

    // Update the time register
    WRITE_REG(RTC->DR,tmp);

    // Leave the initialization mode
    CLEAR_BIT(RTC->ISR, RTC_ISR_INIT);

    // Trigger a synchronization of the shadow registers
    CLEAR_BIT(RTC->ISR, RTC_ISR_RSF);

    // Wait until the shadow registers are synchronized
    while (!READ_BIT(RTC->ISR, RTC_ISR_RSF)) {};

    // Switch the write protection back on
    WRITE_REG(RTC->WPR, 0xFF);
}


void print_RTC_DateTime(RTC_DateTypeDef* Date ,RTC_TimeTypeDef* Time){

	if(Date ==0){
		RTC_DateTypeDef PrintDate;
		RTC_TimeTypeDef PrintTime;
		RTC_read_date(&PrintDate);
		RTC_read_time(&PrintTime);
		UART_printf("%02d.%02d.%04d %02d:%02d:%02d",PrintDate.RTC_Date, PrintDate.RTC_Month, PrintDate.RTC_Year+2000, PrintTime.RTC_Hours, PrintTime.RTC_Minutes, PrintTime.RTC_Seconds);
	}else{
		UART_printf("%02d.%02d.%04d %02d:%02d:%02d",Date->RTC_Date, Date->RTC_Month, Date->RTC_Year+2000, Time->RTC_Hours, Time->RTC_Minutes, Time->RTC_Seconds);
	}
}


void print_RTC_Time(RTC_TimeTypeDef* Time){

	if(Time ==0){
		RTC_TimeTypeDef PrintTime;
		RTC_read_time(&PrintTime);
		UART_printf("%02d:%02d:%02d",PrintTime.RTC_Hours, PrintTime.RTC_Minutes, PrintTime.RTC_Seconds);
	}else{
		UART_printf("%02d:%02d:%02d",Time->RTC_Hours, Time->RTC_Minutes, Time->RTC_Seconds);
	}
}



