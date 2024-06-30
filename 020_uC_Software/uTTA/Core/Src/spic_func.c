/*
 * spic_func.c
 *
 *  Created on: May 4, 2024
 *      Author: wtronics
 */

#include "spi_func.h"


/**
  * @brief SPI3 Initialization Function
  * @param None
  * @retval None
  */
void MX_SPI3_Init(void)
{

  LL_SPI_InitTypeDef SPI_InitStruct = {0};

  LL_GPIO_InitTypeDef GPIO_InitStruct = {0};

  /* Peripheral clock enable */
  LL_APB1_GRP1_EnableClock(LL_APB1_GRP1_PERIPH_SPI3);

  LL_AHB1_GRP1_EnableClock(LL_AHB1_GRP1_PERIPH_GPIOC);
  /**SPI3 GPIO Configuration
  PC10   ------> SPI3_SCK
  PC11   ------> SPI3_MISO
  PC12   ------> SPI3_MOSI
  */
  GPIO_InitStruct.Pin = SD_SPI_SCK_Pin|SD_SPI_MISO_Pin|SD_SPI_MOSI_Pin;
  GPIO_InitStruct.Mode = LL_GPIO_MODE_ALTERNATE;
  GPIO_InitStruct.Speed = LL_GPIO_SPEED_FREQ_HIGH;
  GPIO_InitStruct.OutputType = LL_GPIO_OUTPUT_PUSHPULL;
  GPIO_InitStruct.Pull = LL_GPIO_PULL_NO;
  GPIO_InitStruct.Alternate = LL_GPIO_AF_6;
  LL_GPIO_Init(GPIOC, &GPIO_InitStruct);

  /* SPI3 parameter configuration*/
  SPI_InitStruct.TransferDirection = LL_SPI_FULL_DUPLEX;
  SPI_InitStruct.Mode = LL_SPI_MODE_MASTER;
  SPI_InitStruct.DataWidth = LL_SPI_DATAWIDTH_8BIT;
  SPI_InitStruct.ClockPolarity = LL_SPI_POLARITY_LOW;
  SPI_InitStruct.ClockPhase = LL_SPI_PHASE_1EDGE;
  SPI_InitStruct.NSS = LL_SPI_NSS_SOFT;
  SPI_InitStruct.BaudRate = LL_SPI_BAUDRATEPRESCALER_DIV4;
  SPI_InitStruct.BitOrder = LL_SPI_MSB_FIRST;
  SPI_InitStruct.CRCCalculation = LL_SPI_CRCCALCULATION_DISABLE;
  SPI_InitStruct.CRCPoly = 7;
  LL_SPI_Init(SPI3, &SPI_InitStruct);
  LL_SPI_SetStandard(SPI3, LL_SPI_PROTOCOL_MOTOROLA);
  LL_SPI_DisableNSSPulseMgt(SPI3);

  LL_SPI_Enable(SPI3);

}


uint8_t SPI_TxRx_8b(SPI_TypeDef *hspi, uint8_t tx_byte)
{
	uint8_t	rx_byte;

	// Make sure TXE is set before sending data
	while(LL_SPI_IsActiveFlag_TXE(hspi) == 0);

	// Send tx_byte
	LL_SPI_TransmitData8(hspi, tx_byte);

	// Wait until incoming data has arrived
	while(LL_SPI_IsActiveFlag_RXNE(hspi) == 0);
	// Read data
	rx_byte = LL_SPI_ReceiveData8(hspi);

	return rx_byte;
}


void SPI_TxRx_Buffer(SPI_TypeDef *hspi, uint8_t *TxBuffer, uint16_t TxNBytes, uint8_t *RxBuffer, uint16_t RxNBytes)
{
	uint16_t nTotal = 0;
	if(TxNBytes >RxNBytes)
		nTotal=TxNBytes;
	else
		nTotal=RxNBytes;

	uint16_t nTx = TxNBytes;
	uint16_t nRx = RxNBytes;
	uint8_t TxByte = 0;
	uint8_t RxByte = 0;

	// Read/Write loop

	while(nTotal>0)
	{
		if(nTx >0){
			TxByte = *TxBuffer;
		}else{
			TxByte = 0;
		}

		RxByte = SPI_TxRx_8b(hspi,TxByte);
		if(nRx >0){
			*RxBuffer = RxByte;
			RxBuffer++;
			nRx--;
		}

		if(nTx>0){
			TxBuffer++;
			nTx--;
		}
		nTotal--;
	}
}


void SPI_Tx_Buffer(SPI_TypeDef *hspi, uint8_t *TxBuffer, uint16_t TxNBytes)
{
	uint16_t nTotal = TxNBytes;

	while(nTotal>0)
	{
		SPI_TxRx_8b(hspi,*TxBuffer);
		TxBuffer++;
		nTotal--;
	}
}


void SPI_Rx_Buffer(SPI_TypeDef *hspi, uint8_t *RxBuffer, uint16_t RxNBytes)
{
	uint16_t nTotal = RxNBytes;

	// Read loop

	while(nTotal>0)
	{
		*RxBuffer = SPI_TxRx_8b(hspi,0x00);
		RxBuffer++;
		nTotal--;
	}
}
