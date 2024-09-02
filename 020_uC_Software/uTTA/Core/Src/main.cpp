/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.c
  * @brief          : Main program body
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2024 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* USER CODE END Header */
/* Includes ------------------------------------------------------------------*/
#include "main.h"

/* Private includes ----------------------------------------------------------*/
#include <stdio.h>
#include <ctype.h>
#include <string.h>
#include "SCPI_server.h"
#include "rtc.h"
#include "build_defs.h"
#include "Vrekrer_scpi_parser.hpp"
#include "ErrorCodes.h"
#include "MAX6675.h"


/* Private function prototypes -----------------------------------------------*/

W25QXX_HandleTypeDef w25qxx;

lfs_file_t file;
lfs_t littlefs;

RTC_TimeTypeDef sTime;
RTC_DateTypeDef sDate;

char LogWriteBfr[TX_BFR_SIZE];
uint32_t ADC_Buffer12[ADC_BFR_BLOCKS*ADC_BFR_SIZE] __attribute__((aligned (4)));
uint32_t ADC_Buffer34[ADC_BFR_BLOCKS*ADC_BFR_SIZE] __attribute__((aligned (4)));

volatile uint8_t ADC_PGA_Setting[ADC_BFR_BLOCKS];
volatile uint32_t ADC_TotalBlocks = 0;
volatile uint32_t ADC_CoolingStartBlock = 0;
extern PGA PGA_Gains;
extern volatile Timing SamplingTiming;

uint32_t Meas_RunTime = 0;
uint32_t Meas_StartTime = 0;
int16_t Temp_TypeK[MAX6675_DEVICES];
int GlobalWriteErrorFlag = 0;

volatile MeasurementStates_t FlagMeasurementState = Meas_State_Idle;

uint8_t OperatingMode = MODE_NORMAL;
char DUT_Name[MAX_DUT_NAME_LENGTH] = {"DUT.t3r"};

CH_Def Channels[4] = { 	{"Driver"  , 0, -2600, 0},
						{"Monitor1", 0, -2600, 0},
						{"Monitor2", 0, -2600, 0}};


char TxBuffer[TX_BFR_SIZE];
extern char RxBuffer_Stat[RX_BFR_SIZE];
extern uint8_t RxBuffer_DMA[RX_BFR_SIZE];


//SCPI Function Prototypes
extern SCPI_Parser my_instrument;


/**************************************************************************/
/*!
  * @brief  The application entry point.
  * @retval int
*/
int main(void)
{
  /* MCU Configuration--------------------------------------------------------*/
  /* Reset of all peripherals, Initializes the Flash interface and the Systick. */
  LL_APB2_GRP1_EnableClock(LL_APB2_GRP1_PERIPH_SYSCFG);
  LL_APB1_GRP1_EnableClock(LL_APB1_GRP1_PERIPH_PWR);

  /* System interrupt init*/
  NVIC_SetPriorityGrouping(NVIC_PRIORITYGROUP_0);

  /* Configure the system clock */
  SystemClock_Config();

  // Initialize the timer for 1 ms intervals
  SysTick_Config(SystemCoreClock/1000);

  //LL_SYSTICK_EnableIT();
  LL_mDelay(1000);

  /* Initialize all configured peripherals */
  MX_GPIO_Init();
  MX_RTC_Init();
  MX_DMA_Init();
  MX_USART2_UART_Init();
  MX_ADC3_Init();
  MX_ADC4_Init();
  MX_SPI3_Init();
  MX_TIM1_Init();
  MX_ADC1_Init();
  MX_ADC2_Init();

  Init_MAX6675();

  RTC_DateTypeDef StartupDate;
  RTC_read_date(&StartupDate);
  if(StartupDate.RTC_Year == 0){
	  RTC_write_date_fmt(BUILD_YEAR ,BUILD_MONTH, BUILD_DAY, 1);
	  RTC_write_time_fmt(BUILD_HOUR, BUILD_MIN, BUILD_SEC);
	  UART_printf("Reinitialized RTC\n");
  }

  Enable_ADC_Clock();

  LL_GPIO_ResetOutputPin(PSU_EN_DO_GPIO_Port, PSU_EN_DO_Pin);
  LL_GPIO_ResetOutputPin(PWSTG_EN_DO_GPIO_Port, PWSTG_EN_DO_Pin);

  my_instrument.hash_magic_number = 47; //Default value = 37
  my_instrument.hash_magic_offset = 13;  //Default value = 7
  Init_SCPI_server();

  my_instrument.PrintDebugInfo(USART2);

  UART_printf("Init SD Card!\n");

  if (w25qxx_init(&w25qxx, SPI3, SD_SPI_CS_GPIO_Port, SD_SPI_CS_Pin) == W25QXX_Ok) {
	  UART_printf("W25QXX successfully initialized\n");
	  UART_printf("Manufacturer       = 0x%2x\n", w25qxx.manufacturer_id);
	  UART_printf("Device             = 0x%4x\n", w25qxx.device_id);
	  UART_printf("Block size         = 0x%04x (%lu)\n", w25qxx.block_size, w25qxx.block_size);
	  UART_printf("Block count        = 0x%04x (%lu)\n", w25qxx.block_count, w25qxx.block_count);
	  UART_printf("Total size (in kB) = 0x%04x (%lu)\n", (w25qxx.block_count * w25qxx.block_size) / 1024, (w25qxx.block_count * w25qxx.block_size) / 1024);
  }

  EvalLFSError(w25qxx_littlefs_init(&w25qxx));

  UART_printf("Init completed!\n");
  UART_printf("RTC Time: ");
  print_RTC_DateTime(0,0);
  UART_printf("\n");

  uint32_t LastTempMeasure = GetTick();

  while (1)
  {

	  char* message = my_instrument.GetMessage(USART2, RxBuffer_Stat,"\n");
	  if (message != NULL) {
		  my_instrument.Execute(message, USART2);
	  }
	  DoMeasurement();

	  if(GetTick() > LastTempMeasure){		// Measurement is running
		  LastTempMeasure += MEASURE_TEMP_UPDATE_TIME;

		  for(uint8_t TKidx =0 ; TKidx<MAX6675_DEVICES; TKidx++){
			  Temp_TypeK[TKidx] = Read_MAX6675(TKidx);
		  }
	  }
  }
}


/**************************************************************************/
/*!
    @brief  State machine that controls the measurement
    @param none
    @returns none
*/
/**************************************************************************/
void DoMeasurement(void)
{

	static uint32_t MeasurementStartTime;		// holds the start time of the measurement
	static uint32_t MeasurementNextStepTime;	// the time when the next timestep will be done (roughly)
	static uint8_t ADC_BufferReadBlock;
	static uint32_t Log_WrittenBlocks;
	static uint32_t NextOutput;
	union ADC_conv adc_val;
	int16_t ADC_BFR_idx;
	bool PrintLastADC=false;


	int LFS_ret = 0;

	switch(FlagMeasurementState){
	case Meas_State_Init:					// check for the flag to start the measurement

		ADC_TotalBlocks = 0;
		ADC_CoolingStartBlock = 0;
		ADC_BufferReadBlock =0;
		Log_WrittenBlocks = 0;
		Meas_StartTime = GetTick();
		NextOutput = GetTick();

		EvalLFSError(lfs_file_open(&littlefs, &file, DUT_Name, LFS_O_WRONLY | LFS_O_CREAT | LFS_O_TRUNC));
		if(LFS_ret<0){
			ErrorResponse(ERRC_FILE_SYSTEM, (uint8_t)LFS_ret);
			FlagMeasurementState = Meas_State_Idle;
			break;
		}

		WriteFileHeaderToFile();

		LL_GPIO_SetOutputPin(PSU_EN_DO_GPIO_Port, PSU_EN_DO_Pin); // Enable the output of the Main Power Supply

		SetPGAGain(PGA_Gains.Cooling);
		for(uint8_t PGA_Idx=0; PGA_Idx<ADC_BFR_BLOCKS; PGA_Idx++){
			ADC_PGA_Setting[PGA_Idx] = PGA_Gains.Set;
		}

		//FlagMeasurementState = Meas_State_GDPowerOn;	// Set the step for the StateMachine to the next step

		LL_GPIO_SetOutputPin(PWSTG_PWR_EN_DO_GPIO_Port, PWSTG_PWR_EN_DO_Pin);		// turn on the power of the gate driver
		MeasurementNextStepTime = GetTick()+ 20;
		FlagMeasurementState=Meas_State_GDPowerCheck;

		break;
//	case Meas_State_GDPowerOn:
//
//		HAL_GPIO_WritePin(PWSTG_PWR_EN_DO_GPIO_Port, PWSTG_PWR_EN_DO_Pin, GPIO_PIN_SET);		// turn on the power of the gate driver
//		MeasurementNextStepTime = HAL_GetTick()+ 20;
//		FlagMeasurementState=Meas_State_GPPowerCheck;
//		break;
	case Meas_State_GDPowerCheck:

		if(GetTick()< MeasurementNextStepTime) break;

//		if(HAL_GPIO_ReadPin(PWSTG_UVLO_DI_GPIO_Port, PWSTG_UVLO_DI_Pin) != 1)
//		{
//			ErrorResponse(ERRC_SYSTEM_ERROR, ERST_GATEDRV_UVLO);
//			FlagMeasurementState = Meas_State_Deinit;
//			return;
//		}

		MeasurementStartTime = GetTick();	// Calculate the time when the next Measurement step shall be started
		MeasurementNextStepTime = MeasurementStartTime + SamplingTiming.PreHeatingTime;

		Setup_TIM1(TIM_Mode_Normal);

		SamplingTiming.SetMultiplier = SamplingTiming.MaxTimeMultiplier;
		SamplingTiming.SetSampleTime = (SamplingTiming.FastSampleTime << SamplingTiming.SetMultiplier);
		CalcADCSamplingSettings(SamplingTiming.SetSampleTime);

		Init_ADC_DMA(ADC1_DIODE1_PGA_IN_AI_CH, ADC2_DIODE2_IN_AI_CH, ADC3_DIODE2_IN_AI_CH, ADC4_CURRENT_IN_AI_CH,(uint32_t)&ADC_Buffer12, (uint32_t)&ADC_Buffer34);

		ENABLE_TIMER;						// Enable the timer for ADC sample rate generation

		FlagMeasurementState = Meas_State_Preheating;	// Set the step for the StateMachine to the next step
		break;
	case Meas_State_Preheating:

		if(GetTick()< MeasurementNextStepTime) break;

		MeasurementNextStepTime += SamplingTiming.HeatingTime;
		FlagMeasurementState = Meas_State_PrepHeating;
		break;
	case Meas_State_Heating:

		if(GetTick() < MeasurementNextStepTime)break;

		SamplingTiming.SetMultiplier = 0;
		SamplingTiming.SetSampleTime = SamplingTiming.FastSampleTime;

		CalcADCSamplingSettings(SamplingTiming.SetSampleTime);

		MeasurementNextStepTime += SamplingTiming.CoolingTime;
		FlagMeasurementState = Meas_State_PrepCooling;

		break;
	case Meas_State_Cooling:

		LL_GPIO_ResetOutputPin(PWSTG_PWR_EN_DO_GPIO_Port, PWSTG_PWR_EN_DO_Pin);
		if(GetTick()< MeasurementNextStepTime)break;

		FlagMeasurementState = Meas_State_Deinit;

		break;
	case Meas_State_Deinit:					// cooling time is over, stop the whole system
		DISABLE_TIMER;												// Disable the timer, to stop the ADC
		LL_GPIO_ResetOutputPin(PWSTG_EN_DO_GPIO_Port, PWSTG_EN_DO_Pin);		// Disable the powerstage to shut down the heating current
		LL_GPIO_ResetOutputPin(PSU_EN_DO_GPIO_Port, PSU_EN_DO_Pin);			// Disable the power supply to minimize parasitic effects through the hot powerstage
		FlagMeasurementState = Meas_State_CloseLog;					// Tell the logging routine to write all data including the last block
		//break;
	case Meas_State_CloseLog:
		// Write the rest of the buffer
		do{
			ADC_BufferReadBlock = Log_WrittenBlocks % ADC_BFR_BLOCKS;
			WriteBlockToFile(ADC_BufferReadBlock,Log_WrittenBlocks);
			Log_WrittenBlocks++;
		}while(Log_WrittenBlocks <= ADC_TotalBlocks);

		WriteFileFooterToFile();
		EvalLFSError(lfs_file_sync(&littlefs, &file));
		EvalLFSError(lfs_file_close(&littlefs, &file));

		if( LFS_ret < 0){
			ErrorResponse(ERRC_FILE_SYSTEM, (uint8_t)LFS_ret);
		}

		ADC_CoolingStartBlock =0;
		Log_WrittenBlocks = 0;
		RTC_TimeTypeDef Time;
		RTC_read_time(&Time);
		UART_printf("Measurement completed! ");
		UART_printf("%02u:%02u:%02u\n",Time.RTC_Hours,Time.RTC_Minutes,Time.RTC_Seconds);

		ErrorsOutput();

		FlagMeasurementState = Meas_State_Idle;
		break;
	case Cal_State_Init:					// check for the flag to start the calibration

		LL_GPIO_SetOutputPin(PWSTG_PWR_EN_DO_GPIO_Port, PWSTG_PWR_EN_DO_Pin);		// Enable the gate driver supply
		LL_GPIO_SetOutputPin(PSU_EN_DO_GPIO_Port, PSU_EN_DO_Pin);					// Enable the output of the Main Power Supply

		EvalLFSError(lfs_mkdir(&littlefs,"Cal"));
		EvalLFSError(lfs_file_open(&littlefs, &file, "Cal/CAL.txt", LFS_O_WRONLY | LFS_O_CREAT | LFS_O_TRUNC));
		WriteFileHeaderToFile();
		Setup_TIM1(TIM_Mode_Cal);

		SamplingTiming.SetMultiplier = SamplingTiming.MaxTimeMultiplier;
		SamplingTiming.SetSampleTime = (SamplingTiming.FastSampleTime << SamplingTiming.SetMultiplier);
		CalcADCSamplingSettings(SamplingTiming.SetSampleTime);

		Init_ADC_DMA(ADC1_DIODE1_PGA_IN_AI_CH, ADC2_DIODE2_IN_AI_CH, ADC3_DIODE2_IN_AI_CH, ADC4_CURRENT_IN_AI_CH,(uint32_t)&ADC_Buffer12, (uint32_t)&ADC_Buffer34);

		ENABLE_TIMER;						// Enable the timer for ADC sample rate generation

		MeasurementStartTime = GetTick();	// Calculate the time when the next Measurement step shall be started
		MeasurementNextStepTime = MeasurementStartTime + SamplingTiming.CalSampleTime;

		FlagMeasurementState = Cal_State_Cal;	// Set the step for the StateMachine to the next step

		break;
	case Cal_State_Cal:
		if(GetTick()< MeasurementNextStepTime) break;

		MeasurementNextStepTime += SamplingTiming.CalSampleTime;

		PrintLastADC=true;

		break;
	case Cal_State_DeInit:

		DISABLE_TIMER;									// Disable the timer, to stop the ADC
		LL_GPIO_ResetOutputPin(PWSTG_EN_DO_GPIO_Port, PWSTG_EN_DO_Pin);		// Disable the powerstage to shut down the heating current
		LL_GPIO_ResetOutputPin(PSU_EN_DO_GPIO_Port, PSU_EN_DO_Pin);			// Disable the power supply to minimize parasitic effects through the hot powerstage
		LL_GPIO_ResetOutputPin(PWSTG_PWR_EN_DO_GPIO_Port, PWSTG_PWR_EN_DO_Pin); // Disable the gate driver power supply

		FlagMeasurementState = Meas_State_CloseLog;	 // Set the step for the StateMachine to the next step

		break;
	default:

		break;
	}

	// Data logging loop
	if (FlagMeasurementState){
		if ((ADC_TotalBlocks>0) && (Log_WrittenBlocks < ADC_TotalBlocks) ){
			LD2_GPIO_Port->BSRR = LD2_Pin;

			ADC_BufferReadBlock = Log_WrittenBlocks % ADC_BFR_BLOCKS;	// Calculate the virtual Block number
			if((Log_WrittenBlocks + ADC_BFR_BLOCKS) < ADC_TotalBlocks ){
				//ErrorResponse(ERRC_SYSTEM_ERROR, ERST_ADC_BUFFER_OVERRUN);
			}

			if(WriteBlockToFile(ADC_BufferReadBlock,Log_WrittenBlocks)){
				Log_WrittenBlocks++;
			}
			else{
				ADC_TotalBlocks--;	// Some botch to fix the mysterious behaviour of the 100 samples offset
			}

			LD2_GPIO_Port->BRR = LD2_Pin;
		}

		if(GetTick() > NextOutput){		// Measurement is running
			WriteTemperaturesToFile();

			if((GetTick() - NextOutput) < MEASURE_DATA_UPDATE_TIME){
				NextOutput += MEASURE_DATA_UPDATE_TIME;
			}
			else{	// catch up with the timer
				NextOutput = GetTick() + MEASURE_DATA_UPDATE_TIME;
			}
			Meas_RunTime = GetTick()-Meas_StartTime;
			PrintLastADC=true;
		}
	}

	if(PrintLastADC){

		ADC_BFR_idx = (ADC_BFR_BLOCKS*ADC_BFR_SIZE - DMA1_Channel1->CNDTR)-1;
		if( ADC_BFR_idx <1)
			ADC_BFR_idx = ADC_BFR_BLOCKS*ADC_BFR_SIZE-1;

		adc_val.ADC_Reg = ADC_Buffer12[(uint16_t)ADC_BFR_idx];
		UART_printf("%d;%d;%d;%d;",FlagMeasurementState,ADC_PGA_Setting[(ADC_TotalBlocks)% ADC_BFR_BLOCKS],adc_val.ADC_Val[0],adc_val.ADC_Val[1]);

		adc_val.ADC_Reg = ADC_Buffer34[(uint16_t)ADC_BFR_idx];
		UART_printf("%d;%d",adc_val.ADC_Val[0],adc_val.ADC_Val[1]);

		for(uint8_t TKidx =0; TKidx<MAX6675_DEVICES;TKidx++)
		{
			UART_printf(";%d",Temp_TypeK[TKidx]);
		}
		UART_printf("\n");
	}

	if(LFS_ret<0 || GlobalWriteErrorFlag <0){
		GlobalWriteErrorFlag=0;
		ErrorResponse(ERRC_SYSTEM_ERROR, ERST_FILE_WRITE_ERR);
	}
}

/**************************************************************************/
/*!
    @brief  Writes the file header with all information to the file
    @param none
    @returns none
*/
/**************************************************************************/
int8_t WriteFileHeaderToFile(void){
	int8_t LFS_ret=0;
	/* Writing text */
	RTC_TimeTypeDef Time;
	RTC_DateTypeDef Date;
	RTC_read_date(&Date);
	RTC_read_time(&Time);
	sprintf(LogWriteBfr,"FileVersion;" T3R_FILEVERSION "\n");
	EvalLFSError(LFS_WRITE_STRING(littlefs, file, LogWriteBfr));

	sprintf(LogWriteBfr,"CH1 Name;%s;%ld;%ld;%ld\n",Channels[0].CH_Name,Channels[0].CH_Offs,Channels[0].CH_LinGain,Channels[0].CH_QuadGain);
	EvalLFSError(LFS_WRITE_STRING(littlefs, file, LogWriteBfr));

	sprintf(LogWriteBfr,"CH2 Name;%s;%ld;%ld;%ld\n",Channels[1].CH_Name,Channels[1].CH_Offs,Channels[1].CH_LinGain,Channels[1].CH_QuadGain);
	EvalLFSError(LFS_WRITE_STRING(littlefs, file, LogWriteBfr));

	sprintf(LogWriteBfr,"CH3 Name;%s;%ld;%ld;%ld\n",Channels[2].CH_Name,Channels[2].CH_Offs,Channels[2].CH_LinGain,Channels[2].CH_QuadGain);
	EvalLFSError(LFS_WRITE_STRING(littlefs, file, LogWriteBfr));

	sprintf(LogWriteBfr,"StartTime;%02d:%02d:%02d\n",Time.RTC_Hours,Time.RTC_Minutes,Time.RTC_Seconds);
	EvalLFSError(LFS_WRITE_STRING(littlefs, file, LogWriteBfr));

	sprintf(LogWriteBfr,"StartDate;%02d.%02d.%04d\n",Date.RTC_Date, Date.RTC_Month, ((uint16_t)Date.RTC_Year)+2000);
	EvalLFSError(LFS_WRITE_STRING(littlefs, file, LogWriteBfr));

	sprintf(LogWriteBfr,"Tsamp,fast;%lu\n",SamplingTiming.FastSampleTime);
	EvalLFSError(LFS_WRITE_STRING(littlefs, file, LogWriteBfr));

	sprintf(LogWriteBfr,"Tsamp,low;%lu\n",SamplingTiming.FastSampleTime<<SamplingTiming.MaxTimeMultiplier);
	EvalLFSError(LFS_WRITE_STRING(littlefs, file, LogWriteBfr));

	sprintf(LogWriteBfr,"Samples/Decade;%u\n",ADC_BFR_SIZE);
	EvalLFSError(LFS_WRITE_STRING(littlefs, file, LogWriteBfr));

	sprintf(LogWriteBfr,"Max. Divider;%lu\n",SamplingTiming.MaxTimeMultiplier);
	EvalLFSError(LFS_WRITE_STRING(littlefs, file, LogWriteBfr));

	sprintf(LogWriteBfr,"T_Preheat;%lu\n",SamplingTiming.PreHeatingTime/1000);
	EvalLFSError(LFS_WRITE_STRING(littlefs, file, LogWriteBfr));

	sprintf(LogWriteBfr,"T_Heat;%lu\n",SamplingTiming.HeatingTime/1000);
	EvalLFSError(LFS_WRITE_STRING(littlefs, file, LogWriteBfr));

	sprintf(LogWriteBfr,"T_Cool;%lu\n",SamplingTiming.CoolingTime/1000);
	EvalLFSError(LFS_WRITE_STRING(littlefs, file, LogWriteBfr));

	EvalLFSError(LFS_WRITE_STRING(littlefs, file, "ADC1;ADC2;ADC3;ADC4\n"));

	return LFS_ret;
}


/**************************************************************************/
/*!
    @brief  Writes the file header with all information to the file
    @param none
    @returns none
*/
/**************************************************************************/
int8_t WriteFileFooterToFile(void){
	RTC_TimeTypeDef Time;
	int8_t LFS_ret = 0;

	sprintf(LogWriteBfr,"Cooling Start Block;%lu\nTotal Blocks;%lu\n", ADC_CoolingStartBlock, ADC_TotalBlocks);
	EvalLFSError(LFS_WRITE_STRING(littlefs, file, LogWriteBfr));

	RTC_read_time(&Time);

	sprintf(LogWriteBfr,"Finished;%02u:%02u:%02u\nEnd of Log", Time.RTC_Hours,Time.RTC_Minutes,Time.RTC_Seconds);
	EvalLFSError(LFS_WRITE_STRING(littlefs, file, LogWriteBfr));
	return LFS_ret;
}


/**************************************************************************/
/*!
    @brief  Write function that brings all data from the memory to the SD card
    @param  uint8_t ReadBlock				Block from the circular buffer that will be written to the SD card
    @param  uint32_t TotalWrittenBlocks		Total Number of Blocks written to the SD card
    @returns 1 if block was written, 0 if DMA is still in progress on the requested block
*/
/**************************************************************************/
uint8_t WriteBlockToFile(uint8_t ReadBlock, uint32_t TotalWrittenBlocks)
{
	uint16_t ADC_Idx =0;


	// calculate the borders of the current block
	uint16_t Block_Start = ReadBlock * ADC_BFR_SIZE;
	uint16_t Block_End = (ReadBlock+1) * ADC_BFR_SIZE;

	// read the DMA counter register and calculate the "forward" value
	uint16_t DMA_CurrentPos = (ADC_BFR_BLOCKS*ADC_BFR_SIZE) - DMA1_Channel1->CNDTR;
	int LFS_ret = 0;

	if(DMA_CurrentPos > Block_End || DMA_CurrentPos < Block_Start)	// check if the DMA counter is out of the way...
	{
		// format every sample into a line and print it onto the SD card. (single utoa's are ~50% faster than one sprintf)
		LFS_ret = LFS_WRITE_STRING(littlefs, file, "#B;");	// Block Number

		utoa(TotalWrittenBlocks,LogWriteBfr,10);
		LFS_ret = LFS_WRITE_STRING(littlefs, file, LogWriteBfr);

		LFS_ret = LFS_WRITE_STRING(littlefs, file, ";\n");
		LFS_ret = LFS_WRITE_STRING(littlefs, file, "#P;");	// PGA Setting

		utoa(ADC_PGA_Setting[ReadBlock],LogWriteBfr,10);
		LFS_ret = LFS_WRITE_STRING(littlefs, file, LogWriteBfr);
		LFS_ret = LFS_WRITE_STRING(littlefs, file, ";\n");

		union ADC_conv ADC_RegVal;
		for(ADC_Idx = Block_Start; ADC_Idx < Block_End; ADC_Idx++){

			ADC_RegVal.ADC_Reg = ADC_Buffer12[ADC_Idx];

			utoa(ADC_RegVal.ADC_Val[0],LogWriteBfr,10);
			LFS_ret = LFS_WRITE_STRING(littlefs, file, LogWriteBfr);
			LFS_ret = LFS_WRITE_STRING(littlefs, file, ";");
			utoa(ADC_RegVal.ADC_Val[1],LogWriteBfr,10);
			LFS_ret = LFS_WRITE_STRING(littlefs, file, LogWriteBfr);

			LFS_ret = LFS_WRITE_STRING(littlefs, file, ";");

			ADC_RegVal.ADC_Reg = ADC_Buffer34[ADC_Idx];

			utoa(ADC_RegVal.ADC_Val[0],LogWriteBfr,10);
			LFS_ret = LFS_WRITE_STRING(littlefs, file, LogWriteBfr);
			LFS_ret = LFS_WRITE_STRING(littlefs, file, ";");
			utoa(ADC_RegVal.ADC_Val[1],LogWriteBfr,10);
			LFS_ret = LFS_WRITE_STRING(littlefs, file, LogWriteBfr);
			LFS_ret = LFS_WRITE_STRING(littlefs, file, ";\n");
		}
		if(LFS_ret <0){
			GlobalWriteErrorFlag =1;
		}

		return 1;
	}
	else{
		return 0;
	}
}

/**************************************************************************/
/*!
  * @brief  Writes the latest measured temperatures to the logging file
  * @retval None
*/
uint8_t WriteTemperaturesToFile(void){

	int LFS_ret = 0;

	EvalLFSError(LFS_WRITE_STRING(littlefs, file, "#T;"));	// Thermocouples
	for(uint8_t TKidx =0; TKidx<MAX6675_DEVICES;TKidx++)
	{
		utoa(Temp_TypeK[TKidx],LogWriteBfr,10);
		EvalLFSError(LFS_WRITE_STRING(littlefs, file, LogWriteBfr));
		EvalLFSError(LFS_WRITE_STRING(littlefs, file, ";"));
	}
	EvalLFSError(LFS_WRITE_STRING(littlefs, file, "\n"));

	if(LFS_ret <0){
		GlobalWriteErrorFlag =1;
	}
	return 1;

}




/**************************************************************************/
/*!
    @brief  Function called by the sample clock timer when the preset number of repetitions elapsed
    @param  none
    @returns none
*/
/**************************************************************************/
void SampleClockHandler(void)
{

	ADC_TotalBlocks++;		// one more block written to memory
	ADC_PGA_Setting[(ADC_TotalBlocks)% ADC_BFR_BLOCKS] = PGA_Gains.Set;

	if(FlagMeasurementState == Meas_State_PrepCooling){				// time is over, system will switch to cooling phase
		SetPGAGain(PGA_Gains.Cooling);
		FlagMeasurementState = Meas_State_Cooling;					// switch to cooling
		ADC_CoolingStartBlock = ADC_TotalBlocks;					// save the block no when the cooling phase starts
	}

	if(FlagMeasurementState == Meas_State_Cooling){					// running the cooling phase
		LL_GPIO_ResetOutputPin(PWSTG_EN_DO_GPIO_Port, PWSTG_EN_DO_Pin);		// Disable the powerstage to shut down the heating current
		LL_GPIO_ResetOutputPin(PSU_EN_DO_GPIO_Port, PSU_EN_DO_Pin);			// Disable the power supply to minimize parasitic effects through the hot powerstage

		//PWSTG_PWR_EN_DO_GPIO_Port->BRR = PWSTG_PWR_EN_DO_Pin;		// Disable the power supply of the whole gate driver to save energy

		if(SamplingTiming.SetMultiplier < SamplingTiming.MaxTimeMultiplier){		// Calculate the new timer settings and load them if the timer still needs to slow down
		SamplingTiming.SetMultiplier++;
		SamplingTiming.SetSampleTime = (SamplingTiming.SetSampleTime <<1);
		CalcADCSamplingSettings(SamplingTiming.SetSampleTime);
		}
	}
	if(FlagMeasurementState == Meas_State_PrepHeating){
		SetPGAGain(PGA_Gains.Heating);
		LL_GPIO_SetOutputPin(PWSTG_EN_DO_GPIO_Port, PWSTG_EN_DO_Pin);			// Enable the powerstage
		FlagMeasurementState = Meas_State_Heating;
	}

	return;
}



/**************************************************************************/
/*!
  * @brief  This function is executed in case of error occurrence.
  * @retval None
*/
void Error_Handler(void)
{
  /* USER CODE BEGIN Error_Handler_Debug */
  /* User can add his own implementation to report the HAL error return state */
  __disable_irq();
  while (1)
  {
  }
  /* USER CODE END Error_Handler_Debug */
}

#ifdef  USE_FULL_ASSERT
/**
  * @brief  Reports the name of the source file and the source line number
  *         where the assert_param error has occurred.
  * @param  file: pointer to the source file name
  * @param  line: assert_param error line source number
  * @retval None
  */
void assert_failed(uint8_t *file, uint32_t line)
{
  /* USER CODE BEGIN 6 */
  /* User can add his own implementation to report the file name and line number,
     ex: printf("Wrong parameters value: file %s on line %d\r\n", file, line) */
  /* USER CODE END 6 */
}
#endif /* USE_FULL_ASSERT */
