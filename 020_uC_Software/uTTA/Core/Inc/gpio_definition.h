/*
 * gpio_definition.h
 *
 *  Created on: Oct 14, 2024
 *      Author: wtronics
 */

#ifndef INC_GPIO_DEFINITION_H_
#define INC_GPIO_DEFINITION_H_


#ifdef __cplusplus
extern "C" {
#endif
//Button 1 port
#define Btn_Start_Stop_Pin LL_GPIO_PIN_13
#define Btn_Start_Stop_GPIO_Port GPIOC
// On Board LED
#define LD2_Pin LL_GPIO_PIN_5
#define LD2_GPIO_Port GPIOA


// Debug IO1 port
#define DBG_IO1_Pin LL_GPIO_PIN_0
#define DBG_IO1_GPIO_Port GPIOC
// Debug IO2 port
#define DBG_IO2_Pin LL_GPIO_PIN_1
#define DBG_IO2_GPIO_Port GPIOC
// Debug IO3 port
#define DBG_IO3_Pin LL_GPIO_PIN_2
#define DBG_IO3_GPIO_Port GPIOC
// Debug IO4 port
#define DBG_IO4_Pin LL_GPIO_PIN_3
#define DBG_IO4_GPIO_Port GPIOC
// Debug Pin for Sample time generation timer
#define TIM_DBG_PO_Pin LL_GPIO_PIN_10
#define TIM_DBG_PO_GPIO_Port GPIOA


// Enable Powerstage pin
#define PWSTG_EN_DO_Pin LL_GPIO_PIN_0
#define PWSTG_EN_DO_GPIO_Port GPIOA
// Readback pin of powerstage power supply low
#define PWSTG_UVLO_DI_Pin LL_GPIO_PIN_1
#define PWSTG_UVLO_DI_GPIO_Port GPIOA
// Enable pin of external power supply
#define PSU_EN_DO_Pin LL_GPIO_PIN_4
#define PSU_EN_DO_GPIO_Port GPIOA
// Gate driver power supply enable
#define PWSTG_PWR_EN_DO_Pin LL_GPIO_PIN_0
#define PWSTG_PWR_EN_DO_GPIO_Port GPIOB


// Amplifier Gain Switching outputs
#define GAIN_B0_DO_Pin LL_GPIO_PIN_6
#define GAIN_B0_DO_GPIO_Port GPIOA
#define GAIN_B1_DO_Pin LL_GPIO_PIN_7
#define GAIN_B1_DO_GPIO_Port GPIOA


// Analog inputs for measurement
#define PGA_DIODE3_AI_Pin LL_GPIO_PIN_1
#define PGA_DIODE3_AI_GPIO_Port GPIOB
#define PGA_DIODE2_AI_Pin LL_GPIO_PIN_2
#define PGA_DIODE2_AI_GPIO_Port GPIOB
#define PGA_DIODE1_AI_Pin LL_GPIO_PIN_11
#define PGA_DIODE1_AI_GPIO_Port GPIOB
#define CURR_MEAS_AI_Pin LL_GPIO_PIN_14
#define CURR_MEAS_AI_GPIO_Port GPIOB
#define PGA_DIODE4_AI_Pin LL_GPIO_PIN_15
#define PGA_DIODE4_AI_GPIO_Port GPIOB


// SPI Interface for flash memory
#define FLASH_SPI_SCK_Pin LL_GPIO_PIN_10
#define FLASH_SPI_SCK_GPIO_Port GPIOC
#define FLASH_SPI_MISO_Pin LL_GPIO_PIN_11
#define FLASH_SPI_MISO_GPIO_Port GPIOC
#define FLASH_SPI_MOSI_Pin LL_GPIO_PIN_12
#define FLASH_SPI_MOSI_GPIO_Port GPIOC
#define FLASH_SPI_CS_Pin LL_GPIO_PIN_2
#define FLASH_SPI_CS_GPIO_Port GPIOD


/// Type K temperature sensor  and DAC  SPI + Chip select lines
// SCK Line
#define AUX_SPI_SCK_Pin LL_GPIO_PIN_8
#define AUX_SPI_SCK_GPIO_Port GPIOC
// MISO Line
#define AUX_SPI_MISO_Pin LL_GPIO_PIN_9
#define AUX_SPI_MISO_GPIO_Port GPIOC
// MOSI Line
#define AUX_SPI_MOSI_Pin LL_GPIO_PIN_12
#define AUX_SPI_MOSI_GPIO_Port GPIOA

// CS-Lines for thermocouple transducers
#define AUX_SPI_TC0_CSN_Pin          LL_GPIO_PIN_9
#define AUX_SPI_TC0_CSN_GPIO_Port    GPIOB
#define AUX_SPI_TC1_CSN_Pin          LL_GPIO_PIN_5
#define AUX_SPI_TC1_CSN_GPIO_Port    GPIOC
#define AUX_SPI_TC2_CSN_Pin          LL_GPIO_PIN_8
#define AUX_SPI_TC2_CSN_GPIO_Port    GPIOB
#define AUX_SPI_TC3_CSN_Pin          LL_GPIO_PIN_6
#define AUX_SPI_TC3_CSN_GPIO_Port    GPIOC

// CS-line for DAC
#define AUX_SPI_DAC_CSN_Pin          LL_GPIO_PIN_11
#define AUX_SPI_DAC_CSN_GPIO_Port    GPIOA


// Status LEDs
// Status
#define STATUS_LED_DO_Pin LL_GPIO_PIN_5
#define STATUS_LED_DO_GPIO_Port GPIOB
// Error
#define ERROR_LED_DO_Pin LL_GPIO_PIN_13
#define ERROR_LED_DO_GPIO_Port GPIOB
// Active
#define ACTIVE_LED_DO_Pin LL_GPIO_PIN_10
#define ACTIVE_LED_DO_GPIO_Port GPIOA



// USART RX/TX pins
#define USART_TX_Pin LL_GPIO_PIN_2
#define USART_TX_GPIO_Port GPIOA
#define USART_RX_Pin LL_GPIO_PIN_3
#define USART_RX_GPIO_Port GPIOA


// External debugger connection
#define TMS_Pin LL_GPIO_PIN_13
#define TMS_GPIO_Port GPIOA
#define TCK_Pin LL_GPIO_PIN_14
#define TCK_GPIO_Port GPIOA
#define SWO_Pin LL_GPIO_PIN_3
#define SWO_GPIO_Port GPIOB


#ifndef NVIC_PRIORITYGROUP_0
#define NVIC_PRIORITYGROUP_0         ((uint32_t)0x00000007) /*!< 0 bit  for pre-emption priority,
                                                                 4 bits for subpriority */
#define NVIC_PRIORITYGROUP_1         ((uint32_t)0x00000006) /*!< 1 bit  for pre-emption priority,
                                                                 3 bits for subpriority */
#define NVIC_PRIORITYGROUP_2         ((uint32_t)0x00000005) /*!< 2 bits for pre-emption priority,
                                                                 2 bits for subpriority */
#define NVIC_PRIORITYGROUP_3         ((uint32_t)0x00000004) /*!< 3 bits for pre-emption priority,
                                                                 1 bit  for subpriority */
#define NVIC_PRIORITYGROUP_4         ((uint32_t)0x00000003) /*!< 4 bits for pre-emption priority,
                                                                 0 bit  for subpriority */
#endif

#ifdef __cplusplus
}
#endif

#endif /* INC_GPIO_DEFINITION_H_ */
