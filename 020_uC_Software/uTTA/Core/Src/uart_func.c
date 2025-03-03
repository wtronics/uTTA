/*
 * uart_func.c
 *
 *  Created on: Mar 25, 2023
 *      Author: wtronics
 */

#include "uart_func.h"
//#include "build_defs.h"

#define F_PCLK1 36000000UL			//USART2 Clock Frequency
#define USART2_BAUDRATE 250000UL 	// USART2 Baud Rate


uint8_t Tx2Busy = 0;
char TxMessage[TX_BFR_SIZE];

uint8_t TxCounter = 0;

uint8_t RxBuffer_DMA[RX_BFR_SIZE];

/**
  * @brief USART2 Initialization Function
  * @param None
  * @retval None
  */
void MX_USART2_UART_Init(void)
{

  LL_USART_InitTypeDef USART_InitStruct = {0};

  LL_GPIO_InitTypeDef GPIO_InitStruct = {0};

  /* Peripheral clock enable */
  LL_APB1_GRP1_EnableClock(LL_APB1_GRP1_PERIPH_USART2);

  LL_AHB1_GRP1_EnableClock(LL_AHB1_GRP1_PERIPH_GPIOA);
  /**USART2 GPIO Configuration
  PA2   ------> USART2_TX
  PA3   ------> USART2_RX
  */
  GPIO_InitStruct.Pin = USART_TX_Pin|USART_RX_Pin;
  GPIO_InitStruct.Mode = LL_GPIO_MODE_ALTERNATE;
  GPIO_InitStruct.Speed = LL_GPIO_SPEED_FREQ_LOW;
  GPIO_InitStruct.OutputType = LL_GPIO_OUTPUT_PUSHPULL;
  GPIO_InitStruct.Pull = LL_GPIO_PULL_NO;
  GPIO_InitStruct.Alternate = LL_GPIO_AF_7;
  LL_GPIO_Init(GPIOA, &GPIO_InitStruct);

  /* USART2 DMA Init */

  /* USART2_RX Init */
  LL_DMA_SetDataTransferDirection(DMA1, LL_DMA_CHANNEL_6, LL_DMA_DIRECTION_PERIPH_TO_MEMORY);

  LL_DMA_SetChannelPriorityLevel(DMA1, LL_DMA_CHANNEL_6, LL_DMA_PRIORITY_LOW);

  LL_DMA_SetMode(DMA1, LL_DMA_CHANNEL_6, LL_DMA_MODE_CIRCULAR);

  LL_DMA_SetPeriphIncMode(DMA1, LL_DMA_CHANNEL_6, LL_DMA_PERIPH_NOINCREMENT);

  LL_DMA_SetMemoryIncMode(DMA1, LL_DMA_CHANNEL_6, LL_DMA_MEMORY_INCREMENT);

  LL_DMA_SetPeriphSize(DMA1, LL_DMA_CHANNEL_6, LL_DMA_PDATAALIGN_BYTE);

  LL_DMA_SetMemorySize(DMA1, LL_DMA_CHANNEL_6, LL_DMA_MDATAALIGN_BYTE);

  LL_DMA_ConfigAddresses(DMA1, LL_DMA_CHANNEL_6,(uint32_t)LL_USART_DMA_GetRegAddr(USART2, LL_USART_DMA_REG_DATA_RECEIVE),(uint32_t)RxBuffer_DMA, LL_DMA_GetDataTransferDirection(DMA1, LL_DMA_CHANNEL_6));

  LL_DMA_SetDataLength(DMA1, LL_DMA_CHANNEL_6, sizeof(RxBuffer_DMA));

  LL_DMA_EnableIT_TC(DMA1, LL_DMA_CHANNEL_6);
  LL_DMA_ClearFlag_TC6(DMA1);

  /* USART2_TX Init */
  LL_DMA_SetDataTransferDirection(DMA1, LL_DMA_CHANNEL_7, LL_DMA_DIRECTION_MEMORY_TO_PERIPH);

  LL_DMA_SetChannelPriorityLevel(DMA1, LL_DMA_CHANNEL_7, LL_DMA_PRIORITY_LOW);

  LL_DMA_SetMode(DMA1, LL_DMA_CHANNEL_7, LL_DMA_MODE_NORMAL);

  LL_DMA_SetPeriphIncMode(DMA1, LL_DMA_CHANNEL_7, LL_DMA_PERIPH_NOINCREMENT);

  LL_DMA_SetMemoryIncMode(DMA1, LL_DMA_CHANNEL_7, LL_DMA_MEMORY_INCREMENT);

  LL_DMA_SetPeriphSize(DMA1, LL_DMA_CHANNEL_7, LL_DMA_PDATAALIGN_BYTE);

  LL_DMA_SetMemorySize(DMA1, LL_DMA_CHANNEL_7, LL_DMA_MDATAALIGN_BYTE);

  LL_DMA_EnableIT_TC(DMA1, LL_DMA_CHANNEL_7);
  LL_DMA_ClearFlag_TC7(DMA1);

  USART_InitStruct.BaudRate = 250000;
  USART_InitStruct.DataWidth = LL_USART_DATAWIDTH_8B;
  USART_InitStruct.StopBits = LL_USART_STOPBITS_1;
  USART_InitStruct.Parity = LL_USART_PARITY_NONE;
  USART_InitStruct.TransferDirection = LL_USART_DIRECTION_TX_RX;
  USART_InitStruct.HardwareFlowControl = LL_USART_HWCONTROL_NONE;
  USART_InitStruct.OverSampling = LL_USART_OVERSAMPLING_16;
  LL_USART_Init(USART2, &USART_InitStruct);
  LL_USART_DisableIT_CTS(USART2);
  LL_USART_DisableIT_TC(USART2);
  LL_USART_DisableIT_TXE(USART2);
  LL_USART_ConfigAsyncMode(USART2);

  LL_USART_ClearFlag_IDLE(USART2);
  LL_USART_EnableIT_IDLE(USART2);

  LL_USART_ClearFlag_TC(USART2);

  NVIC_EnableIRQ(USART2_IRQn);

  LL_DMA_EnableChannel(DMA1, 6);
  LL_DMA_EnableChannel(DMA1, 7);

  LL_USART_EnableDMAReq_RX(USART2);

  LL_USART_Enable(USART2);

}


void UART_printf(const char *fmt, ...){

	static char buffer[256];
	va_list args;
	va_start(args, fmt);
	vsnprintf(buffer, sizeof(buffer), fmt, args);
	va_end(args);
	uint16_t TXSize = strlen(buffer);

	while(Tx2Busy == 1){asm("NOP");};

	strcpy(TxMessage, buffer);
	Tx2Busy = 1;

	UART_Transmit_DMA(USART2, (uint8_t*)TxMessage, TXSize);
}


ErrorStatus UART_Transmit_DMA(USART_TypeDef *huart, const uint8_t *pData, uint16_t Size)
{
  /* Check that a Tx process is not already ongoing */

	if ((pData == NULL) || (Size == 0U))
	{
	  return ERROR;
	}
	LL_DMA_DisableChannel(DMA1, LL_DMA_CHANNEL_7);

	LL_DMA_ConfigAddresses(DMA1, LL_DMA_CHANNEL_7, (uint32_t)pData,(uint32_t)LL_USART_DMA_GetRegAddr(USART2, LL_USART_DMA_REG_DATA_TRANSMIT), LL_DMA_GetDataTransferDirection(DMA1, LL_DMA_CHANNEL_7));
	LL_DMA_SetDataLength(DMA1, LL_DMA_CHANNEL_7, Size);


	/* Clear the TC flag in the ICR register */
	LL_USART_ClearFlag_TC(huart);

	/* Enable the DMA transfer for transmit request by setting the DMAT bit
	in the UART CR3 register */
	LL_USART_EnableDMAReq_TX(huart);
	LL_DMA_EnableChannel(DMA1, 7);

	return SUCCESS;
}





