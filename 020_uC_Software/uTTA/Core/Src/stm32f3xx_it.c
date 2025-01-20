/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file    stm32f3xx_it.c
  * @brief   Interrupt Service Routines.
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

/* Includes ------------------------------------------------------------------*/
#include "stm32f3xx_it.h"

/* Private variables ---------------------------------------------------------*/
volatile uint32_t SysTick_counter;
uint8_t RxRollover = 0;
uint8_t RxCounter = 0;
uint16_t RxBfrPos = 0;
char RxBuffer_Stat[RX_BFR_SIZE];

/* External variables --------------------------------------------------------*/
extern uint8_t Tx2Busy;
extern uint8_t RxBuffer_DMA[RX_BFR_SIZE];
/******************************************************************************/
/*           Cortex-M4 Processor Interruption and Exception Handlers          */
/******************************************************************************/
/**
  * @brief This function handles Non maskable interrupt.
  */
void NMI_Handler(void)
{
   while (1)
  {
  }
}

/**
  * @brief This function handles Hard fault interrupt.
  */
void HardFault_Handler(void)
{
  NVIC_SystemReset();
  while (1)
  {
  }
}

/**
  * @brief This function handles Memory management fault.
  */
void MemManage_Handler(void)
{
  while (1)
  {
  }
}

/**
  * @brief This function handles Pre-fetch fault, memory access fault.
  */
void BusFault_Handler(void)
{
  while (1)
  {
  }
}

/**
  * @brief This function handles Undefined instruction or illegal state.
  */
void UsageFault_Handler(void)
{
  while (1)
  {
  }
}

/**
  * @brief This function handles System service call via SWI instruction.
  */
void SVC_Handler(void)
{

}

/**
  * @brief This function handles Debug monitor.
  */
void DebugMon_Handler(void)
{

}

/**
  * @brief This function handles Pendable request for system service.
  */
void PendSV_Handler(void)
{

}

/**
  * @brief This function handles System tick timer.
  */
void SysTick_Handler(void)
{

	SysTick_counter++;
}


uint32_t GetTick(void){
	return SysTick_counter;
}

/******************************************************************************/
/* STM32F3xx Peripheral Interrupt Handlers                                    */
/* Add here the Interrupt Handlers for the used peripherals.                  */
/* For the available peripheral interrupt handler names,                      */
/* please refer to the startup file (startup_stm32f3xx.s).                    */
/******************************************************************************/

/**
  * @brief This function handles DMA1 channel6 global interrupt.
  */
void DMA1_Channel6_IRQHandler(void)
{
	/* USART2_RX */
	LL_DMA_ClearFlag_TC6(DMA1);             /* Clear transfer complete flag */
	RxRollover++;		// increment Rollover Counter
}

/**
  * @brief This function handles DMA1 channel7 global interrupt.
  */
void DMA1_Channel7_IRQHandler(void)
{
	/* USART2_TX */
    /* Check transfer-complete interrupt */
    if (LL_DMA_IsEnabledIT_TC(DMA1, LL_DMA_CHANNEL_7) && LL_DMA_IsActiveFlag_TC7(DMA1)) {
        LL_DMA_ClearFlag_TC7(DMA1);             /* Clear transfer complete flag */
		Tx2Busy = 0;
		return;                     /* Check for data to process */
    }
}

void USART2_IRQHandler(void){
	/* Check for IDLE line interrupt */

	//---------[ UART Data Reception Completion CallBackFunc. ]---------
	// Rx Complete is called by: DMA (automatically), if it rolls over
		// and when an IDLE Interrupt occurs
		// DMA Interrupt allays occurs BEFORE the idle interrupt can be fired because
		// idle detection needs at least one UART clock to detect the bus is idle. So
		// in the case, that the transmission length is one full buffer length
		// and the start buffer pointer is at 0, it will be also 0 at the end of the
		// transmission. In this case the DMA rollover will increment the RxRollover
		// variable first and len will not be zero.
	if (LL_USART_IsEnabledIT_IDLE(USART2) && LL_USART_IsActiveFlag_IDLE(USART2)) {
		LL_USART_ClearFlag_IDLE(USART2);        /* Clear IDLE line flag */

		RxCounter++;																	// increment the Rx Counter

		uint8_t TxSize = 0;
		uint16_t start = RxBfrPos;														// Rx bytes start position (=last buffer position)

		RxBfrPos = RX_BFR_SIZE - (uint16_t)LL_DMA_GetDataLength(DMA1, LL_DMA_CHANNEL_6);				// determine actual buffer position
		uint16_t len = RX_BFR_SIZE;														// init len with max. size

		if(RxRollover < 2)  {
			if(RxRollover) {															// rolled over once
				if(RxBfrPos <= start) len = RxBfrPos + RX_BFR_SIZE - start;				// no bytes overwritten
				else len = RX_BFR_SIZE + 1;												// bytes overwritten error
			} else {
				len = RxBfrPos - start;													// no bytes overwritten
			}
		} else {
			len = RX_BFR_SIZE + 2;														// dual rollover error
		}

		if(len && (len <= RX_BFR_SIZE)) {

			uint8_t i;
			TxSize=strlen(RxBuffer_Stat);

			for(i = 0; i < len; i++) *(RxBuffer_Stat + TxSize+ i) = *(RxBuffer_DMA + ((start + i) % RX_BFR_SIZE));
			*(RxBuffer_Stat + TxSize + i) = 0;

			TxSize =strlen(RxBuffer_Stat);
		} else {
			// buffer overflow error:
			TxSize = strlen(RxBuffer_Stat);
		}

		RxRollover = 0;																	// reset the Rollover variable

	}else {
		// no idle flag? --> DMA rollover occurred
		LL_DMA_ClearFlag_TC6(DMA1);
		RxRollover++;		// increment Rollover Counter
	}
}



void TIM1_UP_TIM16_IRQHandler(void){

	LL_GPIO_SetOutputPin(DBG_IO1_GPIO_Port, DBG_IO1_Pin);
	LL_TIM_ClearFlag_UPDATE(TIM1);//Clear the interrupt flags
	SampleClockHandler();

	LL_GPIO_ResetOutputPin(DBG_IO1_GPIO_Port, DBG_IO1_Pin);
}



void DMA1_Channel1_IRQHandler(void){

}

void DMA2_Channel1_IRQHandler(void){

}


