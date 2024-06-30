/*
 * spi_func.h
 *
 *  Created on: May 4, 2024
 *      Author: wtronics
 */

#ifndef INC_SPI_FUNC_H_
#define INC_SPI_FUNC_H_

#ifdef __cplusplus
extern "C" {
#endif

#include "main.h"

void MX_SPI3_Init(void);
uint8_t SPI_TxRx_8b(SPI_TypeDef *hspi, uint8_t tx_byte);
void SPI_TxRx_Buffer(SPI_TypeDef *hspi, uint8_t *TxBuffer, uint16_t TxNBytes, uint8_t *RxBuffer, uint16_t RxNBytes);
void SPI_Tx_Buffer(SPI_TypeDef *hspi, uint8_t *TxBuffer, uint16_t TxNBytes);
void SPI_Rx_Buffer(SPI_TypeDef *hspi, uint8_t *RxBuffer, uint16_t RxNBytes);

#ifdef __cplusplus
}
#endif

#endif /* INC_SPI_FUNC_H_ */
