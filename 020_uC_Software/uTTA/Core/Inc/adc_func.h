/*
 * adc_func.h
 *
 *  Created on: May 8, 2024
 *      Author: wtronics
 */

#ifndef INC_ADC_FUNC_H_
#define INC_ADC_FUNC_H_

#ifdef __cplusplus
extern "C" {
#endif

#include "config_parameters.h"
#include <stdio.h>
#include <string.h>
#include <stdarg.h>

void MX_ADC1_Init(void);
void MX_ADC2_Init(void);
void MX_ADC3_Init(void);
void MX_ADC4_Init(void);

void Enable_ADC_Clock(void);							// Enables the RCC Clock for all 4 ADCs
void Init_ADC_DMA(uint32_t ADC1_Ch, uint32_t ADC2_Ch, uint32_t ADC3_Ch, uint32_t ADC4_Ch, uint32_t ADC_Buffer12 , uint32_t ADC_Buffer34); // Initializes all 4 ADCs for use with DMA
void ADC_Init(ADC_TypeDef *hADC, uint32_t ADC_Ch);		// Initializes a single ADC to the needed configuration
void Deinit_ADC(void);									// Disables all ADCs and removes their configuration

#ifdef __cplusplus
}
#endif

#endif /* INC_ADC_FUNC_H_ */
