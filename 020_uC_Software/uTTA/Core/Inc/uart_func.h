/*
 * uart_func.h
 *
 *  Created on: Mar 25, 2023
 *      Author: wtronics
 */

#ifndef INC_UART_FUNC_H_
#define INC_UART_FUNC_H_

#ifdef __cplusplus
extern "C" {
#endif

#include "config_parameters.h"
#include "gpio_definition.h"
#include <stdio.h>
#include <string.h>
#include <stdarg.h>


void MX_USART2_UART_Init(void);
void USART2_IRQHandler(void);

ErrorStatus UART_Transmit_DMA(USART_TypeDef *huart, const uint8_t *pData, uint16_t Size);
void UART_printf(const char *fmt, ...);

// UART Buffer Settings
#define RX_BFR_SIZE 80
#define TX_BFR_SIZE 80


#ifdef __cplusplus
}
#endif

#endif /* INC_UART_FUNC_H_ */
