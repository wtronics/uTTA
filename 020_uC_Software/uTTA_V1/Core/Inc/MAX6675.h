/*
 * MAX6675.h
 *
 *  Created on: Apr 24, 2023
 *      Author: wtronics
 */

#ifndef INC_MAX6675_H_
#define INC_MAX6675_H_

#ifdef __cplusplus
extern "C" {
#endif

#include "main.h"


#define MAX6675_DEVICES 4		// Number of MAX6675 connected

void Init_MAX6675(void);					// Initialization routine for MAX6675 Type K converters
int16_t Read_MAX6675(uint8_t DevNo);		// Reads the temperature of the selected MAX6675

typedef struct {
 GPIO_TypeDef* gpio;
 uint16_t pin;
} my_pin_t;

const my_pin_t MAX6675_CS_GPIO[MAX6675_DEVICES] = {{ TEMP_SPI_CSN0_GPIO_Port, TEMP_SPI_CSN0_Pin },{ TEMP_SPI_CSN1_GPIO_Port, TEMP_SPI_CSN1_Pin },{ TEMP_SPI_CSN2_GPIO_Port, TEMP_SPI_CSN2_Pin },{ TEMP_SPI_CSN3_GPIO_Port, TEMP_SPI_CSN3_Pin }};


#ifdef __cplusplus
}
#endif

#endif /* INC_MAX6675_H_ */
