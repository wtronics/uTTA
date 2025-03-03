/*
 * tim_func.c
 *
 *  Created on: May 8, 2024
 *      Author: wtronics
 */

#include "tim_func.h"

TIM_TypeDef htim1;

/**
  * @brief TIM1 Initialization Function
  * @param None
  * @retval None
  */
void MX_TIM1_Init(void)
{

  LL_GPIO_InitTypeDef GPIO_InitStruct = {0};

  LL_AHB1_GRP1_EnableClock(LL_AHB1_GRP1_PERIPH_GPIOA);
  /**TIM1 GPIO Configuration
  PA10   ------> TIM1_CH3
  */
  GPIO_InitStruct.Pin = TIM_DBG_PO_Pin;
  GPIO_InitStruct.Mode = LL_GPIO_MODE_ALTERNATE;
  GPIO_InitStruct.Speed = LL_GPIO_SPEED_FREQ_LOW;
  GPIO_InitStruct.OutputType = LL_GPIO_OUTPUT_PUSHPULL;
  GPIO_InitStruct.Pull = LL_GPIO_PULL_NO;
  GPIO_InitStruct.Alternate = LL_GPIO_AF_6;
  LL_GPIO_Init(TIM_DBG_PO_GPIO_Port, &GPIO_InitStruct);

}



/**************************************************************************/
/*!
    @brief  Setup timer1 as clock for all ADCs to trigger ADC conversions via TRGO event
    @param TIM_Mode_t Mode			Timer mode to be configured (not used)
    @returns none
*/
/**************************************************************************/
void Setup_TIM1(TIM_Mode_t Mode){

	LL_APB2_GRP1_EnableClock(LL_APB2_GRP1_PERIPH_TIM1);	// Enable the clock for Timer1

	LL_TIM_DisableCounter(TIM1);		// Disable Timer 1 before configuration, to be safe
	LL_TIM_DisableIT_UPDATE(TIM1);		// Disable the update interrupt to aviod unwanted interrupts

	LL_TIM_SetCounter(TIM1, 0);			// Reset any existing timer count
	LL_TIM_SetAutoReload(TIM1, 1);		// Set the Auto reload register to some value
	LL_TIM_OC_SetCompareCH1(TIM1, 1);	// Set some value into the capture compare register to get a PWM
	LL_TIM_SetRepetitionCounter(TIM1, ADC_BFR_SIZE-1); // set he repetition counter to 200 repetitions

	LL_TIM_SetPrescaler(TIM1, 71);		// set the prescaler to 71 (counts 0 to 71) division is 72 -> 72MHz/72 = 1MHz
	LL_TIM_SetClockDivision(TIM1, LL_TIM_CLOCKDIVISION_DIV1);	// Reset clock Division bit field to 1
	LL_TIM_SetCounterMode(TIM1, LL_TIM_COUNTERMODE_UP);	// Counting upwards, Only Counter overflow generates update event

	LL_TIM_EnableARRPreload(TIM1);

	LL_TIM_SetTriggerOutput(TIM1, LL_TIM_TRGO_OC1REF); // Set Master Mode selection to Compare Pulse -> Capture Compare 1 will generate a pulse on TRGO for the ADC

	LL_TIM_GenerateEvent_UPDATE(TIM1);	// generate an update to load these values into the timer
	LL_TIM_CC_EnableChannel(TIM1,LL_TIM_CHANNEL_CH1);
	LL_TIM_OC_SetPolarity(TIM1, LL_TIM_CHANNEL_CH1, LL_TIM_OCPOLARITY_HIGH);	// enable the capture compare channel1 (PA8)

	TIM1->SR = 0;					// clear all pending interrupts

	LL_TIM_EnableIT_UPDATE(TIM1);	// Enable the update interrupt

	TIM1->SMCR = RESET;				// No Master-Slave Mode needed Reset everything

	LL_TIM_OC_SetMode(TIM1,LL_TIM_CHANNEL_CH1,LL_TIM_OCMODE_PWM1);	// Set CC1 to PWM mode
	LL_TIM_OC_EnablePreload(TIM1, LL_TIM_CHANNEL_CH1);				// Enable the Compare Preload

	LL_TIM_EnableAllOutputs(TIM1);									// Enable output compare mode
	LL_TIM_ConfigBRK(TIM1,LL_TIM_BREAK_POLARITY_LOW,LL_TIM_BREAK_FILTER_FDIV1);	// set break polarity

//	//Configure the Nested Vector Interrupt Controller
//	//Set 4 bit for preemption (group) priority and 0 bits for sub priority

	//Set priority for timer 1 interrupt to be higher then the other interrupts
	//This is an array of 8 bit registers, of which only the upper 4 bits are used for the priority allowing for 16 levels
	//By grouping this is separated to allow for having sub priorities within a single group.
	//The higher the number the lower the priority
	NVIC_SetPriority(TIM1_UP_TIM16_IRQn,0x20);

	//Enable the timer 1 interrupt
	//This is an array of 32 bit registers, only used to enable an interrupt. To disable the ICER registers need to be used
	//Each register serves 32 interrupts, so to get the register for the interrupt, shift the IRQ number right 5 times (divide by 32) and to get
	//the right interrupt enable bit, shift a unsigned 32 bit integer 1 the IRQ number anded with 31 (modulo 32) times to the right
	NVIC_EnableIRQ(TIM1_UP_TIM16_IRQn);

}


/**************************************************************************/
/*!
    @brief  Calculation of the timing settings for timer1 to create the required sampling rates
    		Caculated values are directly written to timer1 where they will be used as soon as the timer did 250 iterations
    @param uint32_t SampleTime				Sampling Time in 125ns steps (1=125ns, 2=230ns, etc.)
    @returns none
*/
/**************************************************************************/
void CalcADCSamplingSettings(uint32_t SampleTime) // SampleTime in 125ns Steps...
{

	uint32_t calcResCounter = 0;
	uint16_t newPrescaler = PRESCALER_UPSCALE_INITIAL;				//72MHz System Clock with Prescaler = 9 -> 8MHz Timer Clock
	uint32_t PrescalerUpscale = 0;

	do{
		calcResCounter = ((SampleTime)>>PrescalerUpscale);			//multiply by 8 and account for the prescaler upscaling factor
		PrescalerUpscale++;
	}while(calcResCounter > 0xFFF0);									// check that the result fits the 16bit register, if not repeat

	LL_TIM_SetAutoReload(TIM1, (uint16_t)calcResCounter-1);				// Set the Auto reload register to the new period
	LL_TIM_OC_SetCompareCH1(TIM1, (uint16_t)1);							// Set a low value, to be able to see whats going on
	LL_TIM_SetPrescaler(TIM1, (uint16_t)(newPrescaler<<(PrescalerUpscale-1))-1);		// New prescaler
}



