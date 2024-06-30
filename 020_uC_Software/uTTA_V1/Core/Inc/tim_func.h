/*
 * tim_func.h
 *
 *  Created on: May 8, 2024
 *      Author: wtronics
 */

#ifndef INC_TIM_FUNC_H_
#define INC_TIM_FUNC_H_


#ifdef __cplusplus
extern "C" {
#endif

#include "main.h"

typedef enum {
	TIM_Mode_Normal=0,
	TIM_Mode_Cal
}TIM_Mode_t;

#define ENABLE_TIMER 	TIM1->CR1 |= TIM_CR1_CEN
#define DISABLE_TIMER 	TIM1->CR1 &=~ TIM_CR1_CEN


void MX_TIM1_Init(void);								// TIM1 Initialization Function
void Setup_TIM1(TIM_Mode_t Mode);						// Setup timer1 as clock for all ADCs to trigger ADC conversions via TRGO event
void CalcADCSamplingSettings(uint32_t SampleTime);		// Calculation of the timing settings for timer1 to create the required sampling rates


#ifdef __cplusplus
}
#endif


#endif /* INC_TIM_FUNC_H_ */
