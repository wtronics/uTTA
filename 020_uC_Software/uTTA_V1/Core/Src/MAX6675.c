/*
 * MAX6675.c
 *
 *  Created on: Apr 24, 2023
 *      Author: wtronics
 */

#include "MAX6675.h"


/**************************************************************************/
/*!
    @brief  Initialization routine for MAX6675 Type K converters
    @param  none
    @returns none
*/
/**************************************************************************/
void Init_MAX6675(void){

//	LL_GPIO_InitTypeDef GPIO_InitStruct = {0};
//
//  /*Configure GPIO pin : TEMP_SPI_MISO_Pin */
//  GPIO_InitStruct.Pin = TEMP_SPI_MISO_Pin;
//  GPIO_InitStruct.Mode = LL_GPIO_MODE_INPUT;
//  GPIO_InitStruct.Pull = LL_GPIO_PULL_NO;
//  LL_GPIO_Init(TEMP_SPI_MISO_GPIO_Port, &GPIO_InitStruct);
//
//  /*Configure GPIO pins : TEMP_SPI_SCK */
//  GPIO_InitStruct.Pin = TEMP_SPI_SCK_Pin;
//  GPIO_InitStruct.Mode = LL_GPIO_OUTPUT_PUSHPULL;
//  GPIO_InitStruct.Pull = LL_GPIO_PULL_NO;
//  GPIO_InitStruct.Speed = LL_GPIO_SPEED_FREQ_LOW;
//  LL_GPIO_Init(TEMP_SPI_SCK_GPIO_Port, &GPIO_InitStruct);
//
//  for(uint8_t Idx = 0;Idx<MAX6675_DEVICES;Idx++){
//	  /*Configure GPIO pins : TEMP_SPI_CSN0 */
//	  GPIO_InitStruct.Pin = MAX6675_CS_GPIO[Idx].pin;
//	  GPIO_InitStruct.Mode = LL_GPIO_OUTPUT_PUSHPULL;
//	  GPIO_InitStruct.Pull = LL_GPIO_PULL_NO;
//	  GPIO_InitStruct.Speed = LL_GPIO_SPEED_FREQ_LOW;
//	  LL_GPIO_Init(MAX6675_CS_GPIO[Idx].gpio, &GPIO_InitStruct);
//  }

	uint8_t i = 0;
	for(i=0;i<MAX6675_DEVICES;i++){
		LL_GPIO_SetOutputPin(MAX6675_CS_GPIO[i].gpio, MAX6675_CS_GPIO[i].pin);
	}
	LL_GPIO_ResetOutputPin(TEMP_SPI_SCK_GPIO_Port, TEMP_SPI_SCK_Pin);

}


/**************************************************************************/
/*!
    @brief  Reads the temperature of the selected MAX6675
    @param  uint8_t DevNo		// number of the device to read
    @returns int16_t converted temperature in dezi°C. returns -1 if an error occured
*/
/**************************************************************************/
int16_t Read_MAX6675(uint8_t DevNo){

	uint16_t result = 0;
	uint8_t Clk = 0;

	if(DevNo>=MAX6675_DEVICES){
		return -2;
	}
	LL_GPIO_ResetOutputPin(MAX6675_CS_GPIO[DevNo].gpio, MAX6675_CS_GPIO[DevNo].pin);

	for(Clk = 0; Clk <= 15; Clk++){	//Create some Clock fro 16pulses
		LL_GPIO_SetOutputPin(TEMP_SPI_SCK_GPIO_Port, TEMP_SPI_SCK_Pin);

		if(LL_GPIO_IsInputPinSet(TEMP_SPI_MISO_GPIO_Port, TEMP_SPI_MISO_Pin)){
			result |=1;
		}
		result = result <<1;
		LL_GPIO_ResetOutputPin(TEMP_SPI_SCK_GPIO_Port, TEMP_SPI_SCK_Pin);
	}

	if(result & 0x4){
		return  -1;
	}

	LL_GPIO_SetOutputPin(MAX6675_CS_GPIO[DevNo].gpio, MAX6675_CS_GPIO[DevNo].pin);

	return (int16_t)(result>>3);
}
