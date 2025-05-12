/*
 * gpio_func.c
 *
 *  Created on: May 4, 2024
 *      Author: wtronics
 */

#include "gpio_func.h"
/**
  * @brief GPIO Initialization Function
  * @param None
  * @retval None
  */
void MX_GPIO_Init(void)
{
	  LL_EXTI_InitTypeDef EXTI_InitStruct = {0};
	  LL_GPIO_InitTypeDef GPIO_InitStruct = {0};

	  /* GPIO Ports Clock Enable */
	  LL_AHB1_GRP1_EnableClock(LL_AHB1_GRP1_PERIPH_GPIOC);
	  LL_AHB1_GRP1_EnableClock(LL_AHB1_GRP1_PERIPH_GPIOF);
	  LL_AHB1_GRP1_EnableClock(LL_AHB1_GRP1_PERIPH_GPIOA);
	  LL_AHB1_GRP1_EnableClock(LL_AHB1_GRP1_PERIPH_GPIOB);
	  LL_AHB1_GRP1_EnableClock(LL_AHB1_GRP1_PERIPH_GPIOD);


	  /**/
	  LL_GPIO_ResetOutputPin(GPIOA, PWSTG_EN_DO_Pin | PSU_EN_DO_Pin | LD2_Pin | GAIN_B0_DO_Pin | GAIN_B1_DO_Pin | AUX_SPI_MOSI_Pin);

	  /**/
	  LL_GPIO_ResetOutputPin(GPIOB, PWSTG_PWR_EN_DO_Pin|AUX_SPI_TC0_CSN_Pin|AUX_SPI_TC2_CSN_Pin);

	  /**/
	  LL_GPIO_ResetOutputPin(GPIOC, DBG_IO1_Pin|DBG_IO2_Pin|DBG_IO3_Pin|DBG_IO4_Pin|AUX_SPI_TC1_CSN_Pin|AUX_SPI_TC3_CSN_Pin|AUX_SPI_SCK_Pin);

	  /**/
	  LL_GPIO_ResetOutputPin(FLASH_SPI_CS_GPIO_Port, FLASH_SPI_CS_Pin);

	  /**/
	  LL_SYSCFG_SetEXTISource(LL_SYSCFG_EXTI_PORTC, LL_SYSCFG_EXTI_LINE13);

	  /**/
	  LL_SYSCFG_SetEXTISource(LL_SYSCFG_EXTI_PORTC, LL_SYSCFG_EXTI_LINE5);

	  /**/
	  LL_GPIO_SetPinPull(Btn_Start_Stop_GPIO_Port, Btn_Start_Stop_Pin, LL_GPIO_PULL_NO);

	  /**/
	  LL_GPIO_SetPinMode(Btn_Start_Stop_GPIO_Port, Btn_Start_Stop_Pin, LL_GPIO_MODE_INPUT);

	  /**/
	  EXTI_InitStruct.Line_0_31 = LL_EXTI_LINE_13;
	  EXTI_InitStruct.Line_32_63 = LL_EXTI_LINE_NONE;
	  EXTI_InitStruct.LineCommand = ENABLE;
	  EXTI_InitStruct.Mode = LL_EXTI_MODE_IT;
	  EXTI_InitStruct.Trigger = LL_EXTI_TRIGGER_FALLING;
	  LL_EXTI_Init(&EXTI_InitStruct);

	  /**/
	  EXTI_InitStruct.Line_0_31 = LL_EXTI_LINE_5;
	  EXTI_InitStruct.Line_32_63 = LL_EXTI_LINE_NONE;
	  EXTI_InitStruct.LineCommand = ENABLE;
	  EXTI_InitStruct.Mode = LL_EXTI_MODE_IT;
	  EXTI_InitStruct.Trigger = LL_EXTI_TRIGGER_RISING;
	  LL_EXTI_Init(&EXTI_InitStruct);

	  /* PORT C outputs */
	  GPIO_InitStruct.Pin = DBG_IO1_Pin|DBG_IO2_Pin|DBG_IO3_Pin|DBG_IO4_Pin|AUX_SPI_TC1_CSN_Pin|AUX_SPI_TC3_CSN_Pin|AUX_SPI_SCK_Pin;
	  GPIO_InitStruct.Mode = LL_GPIO_MODE_OUTPUT;
	  GPIO_InitStruct.Speed = LL_GPIO_SPEED_FREQ_LOW;
	  GPIO_InitStruct.OutputType = LL_GPIO_OUTPUT_PUSHPULL;
	  GPIO_InitStruct.Pull = LL_GPIO_PULL_NO;
	  LL_GPIO_Init(GPIOC, &GPIO_InitStruct);

	  /* PORT A outputs */
	  GPIO_InitStruct.Pin = PWSTG_EN_DO_Pin | PSU_EN_DO_Pin | LD2_Pin | GAIN_B0_DO_Pin | GAIN_B1_DO_Pin | AUX_SPI_MOSI_Pin | AD56x4_CSN_PIN | ACTIVE_LED_DO_Pin;
	  GPIO_InitStruct.Mode = LL_GPIO_MODE_OUTPUT;
	  GPIO_InitStruct.Speed = LL_GPIO_SPEED_FREQ_LOW;
	  GPIO_InitStruct.OutputType = LL_GPIO_OUTPUT_PUSHPULL;
	  GPIO_InitStruct.Pull = LL_GPIO_PULL_NO;
	  LL_GPIO_Init(GPIOA, &GPIO_InitStruct);

	  /* Port A inputs */
	  GPIO_InitStruct.Pin = PWSTG_PGOOD_DI_Pin;
	  GPIO_InitStruct.Mode = LL_GPIO_MODE_INPUT;
	  GPIO_InitStruct.Pull = LL_GPIO_PULL_NO;
	  LL_GPIO_Init(PWSTG_PGOOD_DI_GPIO_Port, &GPIO_InitStruct);

	  /* PORT B Outputs */
	  GPIO_InitStruct.Pin = PWSTG_PWR_EN_DO_Pin | AUX_SPI_TC0_CSN_Pin | AUX_SPI_TC2_CSN_Pin | STATUS_LED_DO_Pin | ERROR_LED_DO_Pin;
	  GPIO_InitStruct.Mode = LL_GPIO_MODE_OUTPUT;
	  GPIO_InitStruct.Speed = LL_GPIO_SPEED_FREQ_LOW;
	  GPIO_InitStruct.OutputType = LL_GPIO_OUTPUT_PUSHPULL;
	  GPIO_InitStruct.Pull = LL_GPIO_PULL_NO;
	  LL_GPIO_Init(GPIOB, &GPIO_InitStruct);

	  /* PORTD outputs */
	  GPIO_InitStruct.Pin = FLASH_SPI_CS_Pin;
	  GPIO_InitStruct.Mode = LL_GPIO_MODE_OUTPUT;
	  GPIO_InitStruct.Speed = LL_GPIO_SPEED_FREQ_LOW;
	  GPIO_InitStruct.OutputType = LL_GPIO_OUTPUT_PUSHPULL;
	  GPIO_InitStruct.Pull = LL_GPIO_PULL_NO;
	  LL_GPIO_Init(FLASH_SPI_CS_GPIO_Port, &GPIO_InitStruct);

	  /* */
	  GPIO_InitStruct.Pin = AUX_SPI_MISO_Pin;
	  GPIO_InitStruct.Mode = LL_GPIO_MODE_INPUT;
	  GPIO_InitStruct.Pull = LL_GPIO_PULL_NO;
	  LL_GPIO_Init(AUX_SPI_MISO_GPIO_Port, &GPIO_InitStruct);

}

