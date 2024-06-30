/*
 * adc_func.c
 *
 *  Created on: May 8, 2024
 *      Author: wtronics
 */

#include "adc_func.h"

/**
  * @brief ADC1 Initialization Function
  * @param None
  * @retval None
  */
void MX_ADC1_Init(void)
{
  LL_GPIO_InitTypeDef GPIO_InitStruct = {0};

  /* Peripheral clock enable */
  LL_AHB1_GRP1_EnableClock(LL_AHB1_GRP1_PERIPH_ADC12);

  LL_AHB1_GRP1_EnableClock(LL_AHB1_GRP1_PERIPH_GPIOB);
  /**ADC1 GPIO Configuration
  PB11   ------> ADC1_IN14
  */
  GPIO_InitStruct.Pin = PGA_DIODE1_AI_Pin;
  GPIO_InitStruct.Mode = LL_GPIO_MODE_ANALOG;
  GPIO_InitStruct.Pull = LL_GPIO_PULL_NO;
  LL_GPIO_Init(PGA_DIODE1_AI_GPIO_Port, &GPIO_InitStruct);

  /* Enable ADC internal voltage regulator */
  LL_ADC_EnableInternalRegulator(ADC1);
  /* Delay for ADC internal voltage regulator stabilization. */
  /* Compute number of CPU cycles to wait for, from delay in us. */
  /* Note: Variable divided by 2 to compensate partially */
  /* CPU processing cycles (depends on compilation optimization). */
  /* Note: If system core clock frequency is below 200kHz, wait time */
  /* is only a few CPU processing cycles. */
  uint32_t wait_loop_index;
  wait_loop_index = ((LL_ADC_DELAY_INTERNAL_REGUL_STAB_US * (SystemCoreClock / (100000 * 2))) / 10);
  while(wait_loop_index != 0)
  {
    wait_loop_index--;
  }

}

/**
  * @brief ADC2 Initialization Function
  * @param None
  * @retval None
  */
void MX_ADC2_Init(void)
{
  LL_GPIO_InitTypeDef GPIO_InitStruct = {0};

  /* Peripheral clock enable */
  LL_AHB1_GRP1_EnableClock(LL_AHB1_GRP1_PERIPH_ADC12);

  LL_AHB1_GRP1_EnableClock(LL_AHB1_GRP1_PERIPH_GPIOB);
  /**ADC2 GPIO Configuration
  PB2   ------> ADC2_IN12
  */
  GPIO_InitStruct.Pin = PGA_DIODE2_AI_Pin;
  GPIO_InitStruct.Mode = LL_GPIO_MODE_ANALOG;
  GPIO_InitStruct.Pull = LL_GPIO_PULL_NO;
  LL_GPIO_Init(PGA_DIODE2_AI_GPIO_Port, &GPIO_InitStruct);

  /* Enable ADC internal voltage regulator */
  LL_ADC_EnableInternalRegulator(ADC2);
  /* Delay for ADC internal voltage regulator stabilization. */
  /* Compute number of CPU cycles to wait for, from delay in us. */
  /* Note: Variable divided by 2 to compensate partially */
  /* CPU processing cycles (depends on compilation optimization). */
  /* Note: If system core clock frequency is below 200kHz, wait time */
  /* is only a few CPU processing cycles. */
  uint32_t wait_loop_index;
  wait_loop_index = ((LL_ADC_DELAY_INTERNAL_REGUL_STAB_US * (SystemCoreClock / (100000 * 2))) / 10);
  while(wait_loop_index != 0)
  {
    wait_loop_index--;
  }

}

/**
  * @brief ADC3 Initialization Function
  * @param None
  * @retval None
  */
void MX_ADC3_Init(void)
{
  LL_GPIO_InitTypeDef GPIO_InitStruct = {0};

  /* Peripheral clock enable */
  LL_AHB1_GRP1_EnableClock(LL_AHB1_GRP1_PERIPH_ADC34);

  LL_AHB1_GRP1_EnableClock(LL_AHB1_GRP1_PERIPH_GPIOB);
  /**ADC3 GPIO Configuration
  PB1   ------> ADC3_IN1
  */
  GPIO_InitStruct.Pin = PGA_DIODE3_AI_Pin;
  GPIO_InitStruct.Mode = LL_GPIO_MODE_ANALOG;
  GPIO_InitStruct.Pull = LL_GPIO_PULL_NO;
  LL_GPIO_Init(PGA_DIODE3_AI_GPIO_Port, &GPIO_InitStruct);

  /* Enable ADC internal voltage regulator */
  LL_ADC_EnableInternalRegulator(ADC3);
  /* Delay for ADC internal voltage regulator stabilization. */
  /* Compute number of CPU cycles to wait for, from delay in us. */
  /* Note: Variable divided by 2 to compensate partially */
  /* CPU processing cycles (depends on compilation optimization). */
  /* Note: If system core clock frequency is below 200kHz, wait time */
  /* is only a few CPU processing cycles. */
  uint32_t wait_loop_index;
  wait_loop_index = ((LL_ADC_DELAY_INTERNAL_REGUL_STAB_US * (SystemCoreClock / (100000 * 2))) / 10);
  while(wait_loop_index != 0)
  {
    wait_loop_index--;
  }

}

/**
  * @brief ADC4 Initialization Function
  * @param None
  * @retval None
  */
void MX_ADC4_Init(void)
{
  LL_GPIO_InitTypeDef GPIO_InitStruct = {0};

  /* Peripheral clock enable */
  LL_AHB1_GRP1_EnableClock(LL_AHB1_GRP1_PERIPH_ADC34);

  LL_AHB1_GRP1_EnableClock(LL_AHB1_GRP1_PERIPH_GPIOB);
  /**ADC4 GPIO Configuration
  PB14   ------> ADC4_IN4
  PB15   ------> ADC4_IN5
  */
  GPIO_InitStruct.Pin = CURR_MEAS_AI_Pin|PGA_DIODE4_AI_Pin;
  GPIO_InitStruct.Mode = LL_GPIO_MODE_ANALOG;
  GPIO_InitStruct.Pull = LL_GPIO_PULL_NO;
  LL_GPIO_Init(GPIOB, &GPIO_InitStruct);

  /* Enable ADC internal voltage regulator */
  LL_ADC_EnableInternalRegulator(ADC4);
  /* Delay for ADC internal voltage regulator stabilization. */
  /* Compute number of CPU cycles to wait for, from delay in us. */
  /* Note: Variable divided by 2 to compensate partially */
  /* CPU processing cycles (depends on compilation optimization). */
  /* Note: If system core clock frequency is below 200kHz, wait time */
  /* is only a few CPU processing cycles. */
  uint32_t wait_loop_index;
  wait_loop_index = ((LL_ADC_DELAY_INTERNAL_REGUL_STAB_US * (SystemCoreClock / (100000 * 2))) / 10);
  while(wait_loop_index != 0)
  {
    wait_loop_index--;
  }

}

/**************************************************************************/
/*!
    @brief  Enables the RCC Clock for all 4 ADCs
    @param  none
    @returns none
*/
/**************************************************************************/
void Enable_ADC_Clock(void){
	RCC->AHBENR |= RCC_AHBENR_ADC12EN | RCC_AHBENR_ADC34EN;// Enable both ADC clocks
}

/**************************************************************************/
/*!
    @brief  Initializes all 4 ADCs for use with DMA
    @param  uint32_t ADC1_Ch		Channel No of the used ADC1 channel
    @param  uint32_t ADC2_Ch		Channel No of the used ADC2 channel
    @param  uint32_t ADC3_Ch		Channel No of the used ADC3 channel
    @param  uint32_t ADC4_Ch		Channel No of the used ADC4 channel
    @param  uint32_t ADC_Buffer12   Start address of the ADC buffer for ADC1 and ADC2
    @param  uint32_t ADC_Buffer34	Start address of the ADC buffer for ADC3 and ADC4
    @returns none
*/
/**************************************************************************/
void Init_ADC_DMA(uint32_t ADC1_Ch, uint32_t ADC2_Ch, uint32_t ADC3_Ch, uint32_t ADC4_Ch, uint32_t ADC_Buffer12, uint32_t ADC_Buffer34){

	ADC_Init(ADC1, ADC1_Ch);
	ADC_Init(ADC2, ADC2_Ch);

	// Set the ADC12 DMA counter to the size of the ADC Buffer
	LL_DMA_SetDataLength(DMA1, LL_DMA_CHANNEL_1, ADC_BFR_BLOCKS * ADC_BFR_SIZE);

	// Set the peripheral source address to the ADC conversion result register
	LL_DMA_SetPeriphAddress(DMA1, LL_DMA_CHANNEL_1, (uint32_t)&ADC12_COMMON->CDR);

	// Set the target memory address to the ADC buffer
	LL_DMA_SetMemoryAddress(DMA1, LL_DMA_CHANNEL_1, ADC_Buffer12);

	LL_DMA_SetChannelPriorityLevel(DMA1, LL_DMA_CHANNEL_1, LL_DMA_PRIORITY_VERYHIGH);
	LL_DMA_SetMemorySize(DMA1, LL_DMA_CHANNEL_1, LL_DMA_MDATAALIGN_WORD);
	LL_DMA_SetPeriphSize(DMA1, LL_DMA_CHANNEL_1, LL_DMA_PDATAALIGN_WORD);
	LL_DMA_SetMemoryIncMode(DMA1, LL_DMA_CHANNEL_1, LL_DMA_MEMORY_INCREMENT);
	LL_DMA_SetMode(DMA1, LL_DMA_CHANNEL_1, LL_DMA_MODE_CIRCULAR);
	//LL_DMA_EnableIT_TE(DMA1, LL_DMA_CHANNEL_1);

	LL_DMA_ClearFlag_GI1(DMA1); // Clear general global interrupts for DMA1_CH1
	NVIC_SetPriority(DMA1_Channel1_IRQn,15);//(1111b) Group priority 16
	NVIC_EnableIRQ(DMA1_Channel1_IRQn);

	LL_ADC_SetCommonClock(ADC12_COMMON, LL_ADC_CLOCK_SYNC_PCLK_DIV1);
	LL_ADC_SetMultiDMATransfer(ADC12_COMMON, LL_ADC_MULTI_REG_DMA_UNLMT_RES12_10B);
	LL_ADC_SetMultiTwoSamplingDelay(ADC12_COMMON, LL_ADC_MULTI_TWOSMP_DELAY_1CYCLE);
	LL_ADC_SetMultimode(ADC12_COMMON, LL_ADC_MULTI_DUAL_REG_SIMULT);

	LL_ADC_Enable(ADC1);
	LL_ADC_Enable(ADC2);

	LL_ADC_REG_StartConversion(ADC1);
	LL_ADC_REG_StartConversion(ADC2);


	ADC_Init(ADC3, ADC3_Ch);
	ADC_Init(ADC4, ADC4_Ch);

	// Set the ADC34 DMA counter to the size of the ADC Buffer
	LL_DMA_SetDataLength(DMA2, LL_DMA_CHANNEL_5, ADC_BFR_BLOCKS * ADC_BFR_SIZE);

	// Set the peripheral source address to the ADC conversion result register
	LL_DMA_SetPeriphAddress(DMA2, LL_DMA_CHANNEL_5, (uint32_t)&ADC34_COMMON->CDR);

	// Set the target memory address to the ADC buffer
	LL_DMA_SetMemoryAddress(DMA2, LL_DMA_CHANNEL_5, ADC_Buffer34);

	LL_DMA_SetChannelPriorityLevel(DMA2, LL_DMA_CHANNEL_5, LL_DMA_PRIORITY_VERYHIGH);
	LL_DMA_SetMemorySize(DMA2, LL_DMA_CHANNEL_5, LL_DMA_MDATAALIGN_WORD);
	LL_DMA_SetPeriphSize(DMA2, LL_DMA_CHANNEL_5, LL_DMA_PDATAALIGN_WORD);
	LL_DMA_SetMemoryIncMode(DMA2, LL_DMA_CHANNEL_5, LL_DMA_MEMORY_INCREMENT);
	LL_DMA_SetMode(DMA2, LL_DMA_CHANNEL_5, LL_DMA_MODE_CIRCULAR);
	//LL_DMA_EnableIT_TE(DMA2, LL_DMA_CHANNEL_5);

	LL_DMA_ClearFlag_GI5(DMA2); // Clear general global interrupts for DMA2_CH5

	NVIC_SetPriority(DMA2_Channel5_IRQn,14);//(1111b) Group priority 16
	NVIC_EnableIRQ(DMA2_Channel5_IRQn);

	LL_ADC_SetCommonClock(ADC34_COMMON, LL_ADC_CLOCK_SYNC_PCLK_DIV1);
	LL_ADC_SetMultiDMATransfer(ADC34_COMMON, LL_ADC_MULTI_REG_DMA_UNLMT_RES12_10B);
	LL_ADC_SetMultiTwoSamplingDelay(ADC34_COMMON, LL_ADC_MULTI_TWOSMP_DELAY_1CYCLE);
	LL_ADC_SetMultimode(ADC34_COMMON, LL_ADC_MULTI_DUAL_REG_SIMULT);

	LL_ADC_Enable(ADC3);
	LL_ADC_Enable(ADC4);

	LL_ADC_REG_StartConversion(ADC3);
	LL_ADC_REG_StartConversion(ADC4);

	LL_DMA_EnableChannel(DMA1, LL_DMA_CHANNEL_1);		// Enable DMA
	LL_DMA_EnableChannel(DMA2, LL_DMA_CHANNEL_5);		// Enable DMA

	LL_mDelay(1);	// Wait 1ms to get the ADCs stable

	ADC12_COMMON->CSR = 0;
	ADC34_COMMON->CSR = 0;
}


/**************************************************************************/
/*!
    @brief  Initializes a single ADC to the needed configuration
    @param  ADC_HandleTypeDef *hADC				Handle of the ADC to configure
    @param  uint32_t ADC_Ch						Channel No of the used ADC input
    @returns none
*/
/**************************************************************************/
void ADC_Init(ADC_TypeDef *hADC, uint32_t ADC_Ch){


	if(LL_ADC_IsEnabled(hADC))
		LL_ADC_Disable(hADC);

	LL_ADC_InitTypeDef ADC_InitStruct = {0};
	LL_ADC_REG_InitTypeDef ADC_REG_InitStruct = {0};

	hADC->CR = 0;
	hADC->CFGR = 0;// Clear everything

	LL_ADC_EnableInternalRegulator(hADC);		// Enable ADC Voltage regulator

	LL_mDelay(1);	// Wait 1ms to get the ADCs stable

	ADC_InitStruct.Resolution = LL_ADC_RESOLUTION_12B;
	ADC_InitStruct.DataAlignment = LL_ADC_DATA_ALIGN_RIGHT;
	ADC_InitStruct.LowPowerMode = LL_ADC_LP_MODE_NONE;
	LL_ADC_Init(hADC, &ADC_InitStruct);

	ADC_REG_InitStruct.TriggerSource = LL_ADC_REG_TRIG_EXT_TIM1_TRGO;
	ADC_REG_InitStruct.SequencerLength = LL_ADC_REG_SEQ_SCAN_DISABLE;
	ADC_REG_InitStruct.SequencerDiscont = LL_ADC_REG_SEQ_DISCONT_DISABLE;
	ADC_REG_InitStruct.ContinuousMode = LL_ADC_REG_CONV_SINGLE;
	ADC_REG_InitStruct.DMATransfer = LL_ADC_REG_DMA_TRANSFER_LIMITED;
	ADC_REG_InitStruct.Overrun = LL_ADC_REG_OVR_DATA_OVERWRITTEN;
	LL_ADC_REG_Init(hADC, &ADC_REG_InitStruct);

	LL_ADC_SetChannelSamplingTime(hADC, ADC_Ch, LL_ADC_SAMPLINGTIME_19CYCLES_5);// set sampling time for channels 1 to 9 to 19.5 ADC clock cycles
	hADC->SMPR2 = 0x00;	// set sampling time for channels 10 to 18 to 19.5 ADC clock cycles

	hADC->SQR1 = (ADC_Ch<< ADC_SQR1_SQ1_Pos);
	hADC->SQR2 = 0;
	hADC->SQR3 = 0;
	hADC->SQR4 = 0;

	hADC->DIFSEL = 0x00;	// set all ADC channels to single ended mode

	hADC->ISR = 0;			// Clear pending status flags

	LL_ADC_StartCalibration(hADC, LL_ADC_SINGLE_ENDED);
}


/**************************************************************************/
/*!
    @brief  Disables all ADCs and removes their configuration
    @param  none
    @returns none
*/
/**************************************************************************/
void Deinit_ADC(void){

	 //Disable all ADCs
	LL_ADC_Disable(ADC1);
	LL_ADC_Disable(ADC2);
	LL_ADC_Disable(ADC3);
	LL_ADC_Disable(ADC4);

	// Disable DMA
	LL_DMA_DisableChannel(DMA1, LL_DMA_CHANNEL_1);
	LL_DMA_DisableChannel(DMA2, LL_DMA_CHANNEL_5);

	// Clear all control registers
	ADC1->CR  = 0;
	ADC2->CR  = 0;
	ADC3->CR  = 0;
	ADC4->CR  = 0;

	// Clear pending status flags
	ADC1->ISR = 0;
	ADC2->ISR = 0;
	ADC3->ISR = 0;
	ADC4->ISR = 0;
}




