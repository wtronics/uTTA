/*
 * ad56x4.c
 *
 *  Created on: Oct 12, 2024
 *      Author: wmdko
 */

#include "ad56x4.h"


CH_Cal DACCalVal[4];
float DAC_SetVal[4];


/**************************************************************************/
/*!
    @brief  Initialization routine for AD56x4 4channel SPI DACs
    @param  none
    @returns none
*/
/**************************************************************************/
void AD56x4_Init(CH_Cal CalValues[]){



	for(uint8_t idx=0;idx<4;idx++){
		DACCalVal[idx] = CalValues[idx];
		UART_printf("CAL %d, %f, %f, %f\n",idx, DACCalVal[idx].Offset, DACCalVal[idx].LinGain, DACCalVal[idx].CubGain);
	}

	LL_GPIO_SetOutputPin(AD56x4_CSN_PORT, AD56x4_CSN_PIN);
	LL_GPIO_ResetOutputPin(AD56x4_SCK_PORT, AD56x4_SCK_PIN);

	AD56x4_write(AD56X4_CMD_RESET, 1);
	AD56x4_write(AD56X4_CMD_POWER_UPDOWN, AD56X4_CH_ALL);
	AD56x4_write(AD56X4_CMD_WRITE_INPUT_REG | AD56X4_CH_A, 0);
	AD56x4_write(AD56X4_CMD_WRITE_INPUT_REG | AD56X4_CH_B, 0);
	AD56x4_write(AD56X4_CMD_WRITE_INPUT_REG | AD56X4_CH_C, 0);
	AD56x4_write(AD56X4_CMD_WRITE_INPUT_REG | AD56X4_CH_D, 0);
	AD56x4_write(AD56X4_CMD_WRITE_INPUT_REG_UPDATE_ALL, 0);



}



void AD56x4_write(uint8_t cmd, uint16_t value){

	LL_GPIO_ResetOutputPin(AD56x4_CSN_PORT, AD56x4_CSN_PIN);

	AD56x4_write_byte(cmd);
	AD56x4_write_byte((uint8_t)HIGH_BYTE(value));
	AD56x4_write_byte((uint8_t)LOW_BYTE(value));

	LL_GPIO_SetOutputPin(AD56x4_CSN_PORT, AD56x4_CSN_PIN);
	LL_GPIO_ResetOutputPin(AD56x4_MOSI_PORT, AD56x4_MOSI_PIN);

}

void AD56x4_write_byte(uint8_t cmd){
	int8_t Clk = 0;

	for(Clk = 7; Clk >=0 ; Clk--){	//Create some Clock for 16pulses
		if(cmd & (1<<Clk)){
			LL_GPIO_SetOutputPin(AD56x4_MOSI_PORT, AD56x4_MOSI_PIN);
		}else{
			LL_GPIO_ResetOutputPin(AD56x4_MOSI_PORT, AD56x4_MOSI_PIN);
		}

		LL_GPIO_SetOutputPin(AD56x4_SCK_PORT, AD56x4_SCK_PIN);

		LL_GPIO_ResetOutputPin(AD56x4_SCK_PORT, AD56x4_SCK_PIN);
	}

}

void AD56x4_write_channel_direct(uint8_t ch, uint16_t value){
	if(ch < 4){
		AD56x4_write(AD56X4_CMD_WRITE_UPDATE_CH | ch, value);
	}
}


int8_t AD56x4_WriteChannelCalibrated(uint8_t ch, float value){
	if(ch < 4){
		if(CalAvailable != 1){
			// no calibration is available, therefore the setup will be done without scaling
			AD56x4_write(AD56X4_CMD_WRITE_UPDATE_CH | ch, (uint16_t)value);
			return 2;
		}else{
			int32_t DAC_SetValue = 0;
			DAC_SetVal[ch] = value;
			// scale the value using the calibration factors
			DAC_SetValue =(int32_t)((value-DACCalVal[ch].Offset)/ DACCalVal[ch].LinGain);
			if((DAC_SetValue >=0) && (DAC_SetValue <65536)){
				AD56x4_write(AD56X4_CMD_WRITE_UPDATE_CH | ch, (uint16_t)DAC_SetValue);
				return 1;
			}
			return -2;
		}
	}
	return -1;
}


void AD56x4_SetDefaultOutput(void){
	if(CalAvailable==1){
		AD56x4_WriteChannelCalibrated(CH_ISEN, ISEN_DEF_VALUE_mA);
		AD56x4_WriteChannelCalibrated(CH_VOffs0, VOFFS0_DEF_VALUE_V);
		AD56x4_WriteChannelCalibrated(CH_VOffs1_3, VOFFS1_3_DEF_VALUE_V);

	}else{
		AD56x4_WriteChannelCalibrated(CH_ISEN, ISEN_DEF_VALUE_RAW);
		AD56x4_WriteChannelCalibrated(CH_VOffs0, VOFFS0_DEF_VALUE_RAW);
		AD56x4_WriteChannelCalibrated(CH_VOffs1_3, VOFFS1_3_DEF_VALUE_RAW);
	}
}

