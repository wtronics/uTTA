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

#include "config_parameters.h"
#include "gpio_definition.h"


#define MAX6675_DEVICES 4		// Number of MAX6675 connected

void Init_MAX6675(void);					// Initialization routine for MAX6675 Type K converters
float Read_MAX6675(uint8_t DevNo);		// Reads the temperature of the selected MAX6675

typedef struct {
 GPIO_TypeDef* gpio;
 uint16_t pin;
} my_pin_t;

const my_pin_t MAX6675_CS_GPIO[MAX6675_DEVICES] = {{ AUX_SPI_TC0_CSN_GPIO_Port, AUX_SPI_TC0_CSN_Pin },{ AUX_SPI_TC1_CSN_GPIO_Port, AUX_SPI_TC1_CSN_Pin },{ AUX_SPI_TC2_CSN_GPIO_Port, AUX_SPI_TC2_CSN_Pin },{ AUX_SPI_TC3_CSN_GPIO_Port, AUX_SPI_TC3_CSN_Pin }};


#ifdef __cplusplus
}
#endif

#endif /* INC_MAX6675_H_ */
