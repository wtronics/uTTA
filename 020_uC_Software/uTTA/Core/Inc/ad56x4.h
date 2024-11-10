/*
 * adc_func.h
 *
 *  Created on: May 8, 2024
 *      Author: wtronics
 */

#ifndef INC_AD56X4_H_
#define INC_AD56X4_H_


#ifdef __cplusplus
extern "C" {
#endif

#include "config_parameters.h"
#include "gpio_definition.h"
#include "dev_cal.h"

#include <stdio.h>
#include <string.h>
#include <stdarg.h>

/* Command bits
   | C2 | C1 | C0 | Command
   ------------------------------------------------------------
   | 0  | 0  | 0  | Write to input register N
   | 0  | 0  | 1  | Update DAC register N
   | 0  | 1  | 0  | Write to input register N and update on all
   | 0  | 1  | 1  | Write to and update channel N
   | 1  | 0  | 0  | Power up-down
   | 1  | 0  | 1  | Reset
   | 1  | 1  | 0  | Set LDAC register
   | 1  | 1  | 1  | Internal reference on/off (if present)
   ------------------------------------------------------------

   Address bits
   | A2 | A1 | A0 | Channel/s
   --------------------------
   | 0  | 0  | 0  | A
   | 0  | 0  | 1  | B
   | 0  | 1  | 0  | C
   | 0  | 1  | 1  | D
   | 1  | 1  | 1  | All
   --------------------------

   For the power up-down command, the power mode specified with
   data bits DB5 and DB4 are applied to the channels specified by
   ones in the bit mask made by DB3 to DB0 (in channel D to A
   order). The power modes are

   Power up-down mode
   | DB5 | DB4 | mode
   ------------------------------
   |  0  |  0  | normal operation
   |  0  |  1  | 1k to ground
   |  1  |  0  | 100k to ground
   |  1  |  1  | tri-state
   ------------------------------

   For the reset command, DB0 controls exactly what is reset.
   Regardless of its value, the input and DAC registers are all
   reset to zero. If DB0 is set to one; then the LDAC register
   is reset to zero, all channels powered up to normal mode, and
   the internal reference turned off (means external reference is
   used).

   For the set LDAC register command, whether to just set the DAC
   register to the input register every time it is changed or not,
   is set for each channel with DB3 to DB0 corresponding to channel
   D through A. A zero means that setting the input register does
   not automatically set the DAC register (value isn't written out
   as output yet) and a one means that the DAC register (and hence
   the output) is set the the input register the moment the input
   register is changed.

   For the internal reference on/off command, setting DB0 to zero
   turns it off and setting it to one turns it on. When off, the
   external reference is used as the voltage reference. This
   command only works in the R versions that have an internal
   reference.

   */

#define AD56x4_CSN_PORT		AUX_SPI_DAC_CSN_GPIO_Port
#define AD56x4_CSN_PIN		AUX_SPI_DAC_CSN_Pin
#define AD56x4_SCK_PORT		AUX_SPI_SCK_GPIO_Port
#define AD56x4_SCK_PIN		AUX_SPI_SCK_Pin
#define AD56x4_MOSI_PORT	AUX_SPI_MOSI_GPIO_Port
#define AD56x4_MOSI_PIN		AUX_SPI_MOSI_Pin

#define AD56X4_CMD_WRITE_INPUT_REG            0x00
#define AD56X4_CMD_UPDATE_DAC_REG             0x08
#define AD56X4_CMD_WRITE_INPUT_REG_UPDATE_ALL 0x10
#define AD56X4_CMD_WRITE_UPDATE_CH            0x18
#define AD56X4_CMD_POWER_UPDOWN               0x20
#define AD56X4_CMD_RESET                      0x28
#define AD56X4_CMD_SET_LDAC                   0x30
#define AD56X4_CMD_REF_ONOFF                  0x38

#define AD56X4_CH_A                           0x00
#define AD56X4_CH_B                           0x01
#define AD56X4_CH_C                           0x02
#define AD56X4_CH_D                           0x03
#define AD56X4_CH_ALL                         0x07

#define AD56X4_SETMODE_INPUT                  AD56X4_CMD_WRITE_INPUT_REG
#define AD56X4_SETMODE_INPUT_DAC              AD56X4_CMD_WRITE_UPDATE_CH
#define AD56X4_SETMODE_INPUT_DAC_ALL          AD56X4_CMD_WRITE_INPUT_REG_UPDATE_ALL

#define AD56X4_PMODE_NORMAL               0x00
#define AD56X4_PMODE_PWRDN_1K             0x10
#define AD56X4_PMODE_PWRDN_100K           0x20
#define AD56X4_PMODE_HIZ                  0x30

#define LOW_BYTE(x)        (x & 0xff)			// extract Low Byte from uint16_t
#define HIGH_BYTE(x)       ((x >> 8) & 0xff)	// extract High Byte from uint16_t

typedef enum DAC_Channel_Alias{
	CH_ISEN,		// Sense Current calibration
	CH_Spare,		// This is just a spare channel
	CH_VOffs0,		// Offset Voltage calibration of the heated channel
	CH_VOffs1_3 	// Offset Voltage calibration of all monitor channels
}DAC_Ch_t;

void AD56x4_Init(CH_Cal CalValues[]);
void AD56x4_write(uint8_t cmd, uint16_t value);
void AD56x4_write_byte(uint8_t cmd);
void AD56x4_write_channel_direct(DAC_Ch_t ch, uint16_t value);
int8_t AD56x4_WriteChannelCalibrated(DAC_Ch_t ch, float value);
void AD56x4_SetDefaultOutput(void);


extern float DAC_SetVal[4];


#ifdef __cplusplus
}
#endif

#endif /* INC_AD56X4_H_ */
