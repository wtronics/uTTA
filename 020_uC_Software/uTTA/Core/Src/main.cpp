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
#include <main.hpp>
#include "Vrekrer_scpi_parser.hpp"
#include "MAX6675.h"
#include "SCPI_server.h"
#include "dev_cal.h"

/* Private function prototypes -----------------------------------------------*/

W25QXX_HandleTypeDef w25qxx;

lfs_file_t file;
lfs_t littlefs;

char LogWriteBfr[TX_BFR_SIZE];
uint32_t ADC_Buffer12[ADC_BFR_BLOCKS*ADC_BFR_SIZE] __attribute__((aligned (4)));
uint32_t ADC_Buffer34[ADC_BFR_BLOCKS*ADC_BFR_SIZE] __attribute__((aligned (4)));

volatile uint8_t ADC_PGA_Setting[ADC_BFR_BLOCKS];
volatile int32_t ADC_TotalBlocks = 0;
volatile int32_t ADC_CoolingStartBlock = 0;
PGA_t PGA_Gains = {PGA_DEF_GAIN, PGA_DEF_GAIN, PGA_DEF_GAIN};
volatile Timing_t SamplingTiming = {ADC_DEF_SAMPLETIME, 0.0f, ADC_MAX_MULTIPLIER, ADC_MAX_SAMPLERATE << ADC_MAX_MULTIPLIER, ADC_MAX_MULTIPLIER, MEAS_DEF_PREHEATING_TIME, MEAS_DEF_HEATING_TIME, MEAS_DEF_COOLING_TIME, TEST_DEF_SAMPLE_TIME};


uint32_t Meas_RunTime = 0;
uint32_t Meas_StartTime = 0;
float Temp_TypeK[MAX6675_DEVICES];
int GlobalWriteErrorFlag = 0;
int FlashMemoryAvailable = 0;

volatile MeasurementStates_t FlagMeasurementState = Meas_State_Idle;

DeviceModes_t OperatingMode = Mode_Normal;
char DUT_Name[MAX_DUT_NAME_LENGTH] = {"DUT.umf"};

CH_Def Channels[4] = { 	{"Driver"  , 0, -2600, 0},
						{"Monitor1", 0, -2600, 0},
						{"Monitor2", 0, -2600, 0},
						{"Spare"   , 0, -2600, 0}};


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
  LL_mDelay(500);

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
  }

  Enable_ADC_Clock();

  LL_GPIO_ResetOutputPin(PSU_EN_DO_GPIO_Port, PSU_EN_DO_Pin);
  LL_GPIO_ResetOutputPin(PWSTG_EN_DO_GPIO_Port, PWSTG_EN_DO_Pin);

  // needs some tweaking to get the hashes free from overlaps and collisions
  my_instrument.hash_magic_number = 53; //Default value = 37
  my_instrument.hash_magic_offset = 3;  //Default value = 7
  Init_SCPI_server();

  my_instrument.PrintDebugInfo(USART2, 0);

  INIT_DBG("Init SD Card!\n");
  uint32_t TotalMem=0;

  if (w25qxx_init(&w25qxx, SPI3, FLASH_SPI_CS_GPIO_Port, FLASH_SPI_CS_Pin) == W25QXX_Ok) {
	  INIT_DBG("W25QXX successfully initialized\n");
	  INIT_DBG("Manufacturer       = 0x%2x\n", w25qxx.manufacturer_id);
	  INIT_DBG("Device             = 0x%4x\n", w25qxx.device_id);
	  INIT_DBG("Block size         = 0x%04x (%lu)\n", w25qxx.block_size, w25qxx.block_size);
	  INIT_DBG("Block count        = 0x%04x (%lu)\n", w25qxx.block_count, w25qxx.block_count);
	  INIT_DBG("Total size (in kB) = 0x%04x (%lu)\n", (w25qxx.block_count * w25qxx.block_size) / 1024, (w25qxx.block_count * w25qxx.block_size) / 1024);

	  EvalLFSError(w25qxx_littlefs_init(&w25qxx));

	  lfs_mem_size(&littlefs, "/", &TotalMem);
	  DBG_LVL1("Total size used memory = %lu bytes\n", TotalMem);
	  uint32_t lfs_used_bytes =  lfs_fs_size(&littlefs)*0xffff;
	  DBG_LVL1("Total size used blocks = %lu blocks, %lu bytes\n", lfs_fs_size(&littlefs), lfs_used_bytes);

	  Read_CalibrationFromFlash(&littlefs, &file, 0);

	  FlashMemoryAvailable = 1;
  }
  else{
	  ErrorResponse(ERRC_SYSTEM_ERROR, ERST_NO_FLASH_MEMORY);
	  FlashMemoryAvailable = -1;
  }

  AD56x4_Init(&ChannelCalibValues[DAC_Ch_ISEN]);
  AD56x4_SetDefaultOutput();

  UART_printf("RTC Time: ");
  print_RTC_DateTime(0,0);
  UART_printf("\n");

  uint32_t LastTempMeasure = GetTick();

  while (1)
  {

	  char* message = my_instrument.GetMessage(USART2, RxBuffer_Stat,"\n");
	  if (message != NULL) {
		  if(my_instrument.comm_mode == CommMode_SCPI){
			  my_instrument.Execute(message, USART2);
		  }else{
			  FileUpload_SerialToFile(message);
		  }

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
	static int32_t Log_WrittenBlocks;
	static uint32_t NextOutput;
	union ADC_conv adc_val;
	int16_t ADC_BFR_idx;
	bool PrintLastADC=false;
	RTC_TimeTypeDef Time;


	int LFS_ret = 0;

	switch(FlagMeasurementState){
	case Meas_State_Init:					// check for the flag to start the measurement

		ADC_TotalBlocks = 0;
		ADC_CoolingStartBlock = 0;
		ADC_BufferReadBlock =0;
		Log_WrittenBlocks = 0;
		Meas_StartTime = GetTick();
		NextOutput = GetTick();

		if(FlashMemoryAvailable <= 0){	// no flash memory is attached to save measurement data therefore the measurement is aborted
			ErrorResponse(ERRC_FILE_SYSTEM, ERST_NO_FLASH_MEMORY);
			FlagMeasurementState = Meas_State_Idle;
			break;
		}
		if(CalAvailable < 1){		// No valid calibration file was found therefore the measurement is aborted
			ErrorResponse(ERRC_SYSTEM_ERROR, ERST_NO_CALIBRATION);
			FlagMeasurementState = Meas_State_Idle;
			break;
		}

		EvalLFSError(lfs_file_open(&littlefs, &file, DUT_Name, LFS_O_WRONLY | LFS_O_CREAT | LFS_O_TRUNC));
		if(LFS_ret<0){
			ErrorResponse(ERRC_FILE_SYSTEM, (uint8_t)LFS_ret);
			FlagMeasurementState = Meas_State_Idle;
			break;
		}
		CheckMemoryFileFit();

		WriteFileHeaderToFile(&littlefs, &file);

		LL_GPIO_SetOutputPin(PSU_EN_DO_GPIO_Port, PSU_EN_DO_Pin); // Enable the output of the Main Power Supply

		SetPGAGain(PGA_Gains.Cooling);
		for(uint8_t PGA_Idx=0; PGA_Idx<ADC_BFR_BLOCKS; PGA_Idx++){
			ADC_PGA_Setting[PGA_Idx] = PGA_Gains.Set;
		}

		LL_GPIO_SetOutputPin(PWSTG_PWR_EN_DO_GPIO_Port, PWSTG_PWR_EN_DO_Pin);		// turn on the power of the gate driver
		MeasurementNextStepTime = GetTick()+ 20;
		FlagMeasurementState=Meas_State_GDPowerCheck;

		break;
	case Meas_State_GDPowerCheck:

		if(GetTick()< MeasurementNextStepTime) break;
#ifdef EARLY_HW_POWER_BOARD
		if(LL_GPIO_IsInputPinSet(PWSTG_PGOOD_DI_GPIO_Port, PWSTG_PGOOD_DI_Pin))
#else
		if(!LL_GPIO_IsInputPinSet(PWSTG_PGOOD_DI_GPIO_Port, PWSTG_PGOOD_DI_Pin))
#endif
		{
			ErrorResponse(ERRC_SYSTEM_ERROR, ERST_GATEDRV_UVLO);
			FlagMeasurementState = Meas_State_Deinit;
			break;
		}

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

		if( SamplingTiming.HeatingTime > 0){		// check if this is a real measurement or just a calibration run
			MeasurementNextStepTime += SamplingTiming.HeatingTime;
			FlagMeasurementState = Meas_State_PrepHeating;
		}else		// Just a calibration measurement
		{
			FlagMeasurementState = Meas_State_Deinit;
			ADC_CoolingStartBlock = -1;
		}
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

		WriteFileFooterToFile(&littlefs, &file, ADC_CoolingStartBlock, ADC_TotalBlocks);
		EvalLFSError(lfs_file_sync(&littlefs, &file));
		EvalLFSError(lfs_file_close(&littlefs, &file));

		if( LFS_ret < 0){
			ErrorResponse(ERRC_FILE_SYSTEM, (uint8_t)LFS_ret);
		}

		ADC_CoolingStartBlock =0;
		Log_WrittenBlocks = 0;
		RTC_read_time(&Time);
		UART_printf("Measurement completed!\n");

		FlagMeasurementState = Meas_State_Idle;
		break;
	case Test_State_Init:					// check for the flag to start the calibration

		if(FlashMemoryAvailable <= 0){
			ErrorResponse(ERRC_FILE_SYSTEM, ERST_NO_FLASH_MEMORY);
			FlagMeasurementState = Meas_State_Idle;
			break;
		}

		LL_GPIO_SetOutputPin(PWSTG_PWR_EN_DO_GPIO_Port, PWSTG_PWR_EN_DO_Pin);		// Enable the gate driver supply
		LL_GPIO_SetOutputPin(PSU_EN_DO_GPIO_Port, PSU_EN_DO_Pin);					// Enable the output of the Main Power Supply

		Setup_TIM1(TIM_Mode_Cal);

		SamplingTiming.SetMultiplier = SamplingTiming.MaxTimeMultiplier;
		SamplingTiming.SetSampleTime = (SamplingTiming.FastSampleTime << SamplingTiming.SetMultiplier);
		CalcADCSamplingSettings(SamplingTiming.SetSampleTime);

		Init_ADC_DMA(ADC1_DIODE1_PGA_IN_AI_CH, ADC2_DIODE2_IN_AI_CH, ADC3_DIODE2_IN_AI_CH, ADC4_CURRENT_IN_AI_CH,(uint32_t)&ADC_Buffer12, (uint32_t)&ADC_Buffer34);

		ENABLE_TIMER;						// Enable the timer for ADC sample rate generation

		MeasurementStartTime = GetTick();	// Calculate the time when the next Measurement step shall be started
		MeasurementNextStepTime = MeasurementStartTime + SamplingTiming.TestSampleTime;

		FlagMeasurementState = Test_State_Cal;	// Set the step for the StateMachine to the next step

		break;
	case Test_State_Cal:
		if(GetTick()< MeasurementNextStepTime) break;

		MeasurementNextStepTime += SamplingTiming.TestSampleTime;

		PrintLastADC=true;

		break;
	case Test_State_DeInit:

		DISABLE_TIMER;									// Disable the timer, to stop the ADC
		LL_GPIO_ResetOutputPin(PWSTG_EN_DO_GPIO_Port, PWSTG_EN_DO_Pin);		// Disable the powerstage to shut down the heating current
		LL_GPIO_ResetOutputPin(PSU_EN_DO_GPIO_Port, PSU_EN_DO_Pin);			// Disable the power supply to minimize parasitic effects through the hot powerstage
		LL_GPIO_ResetOutputPin(PWSTG_PWR_EN_DO_GPIO_Port, PWSTG_PWR_EN_DO_Pin); // Disable the gate driver power supply

		FlagMeasurementState = Test_State_Exit;	 // Set the step for the StateMachine to the next step

		break;
	case Test_State_Exit:

		ADC_CoolingStartBlock =0;
		Log_WrittenBlocks = 0;

		RTC_read_time(&Time);
		UART_printf("Measurement completed! \n");

		FlagMeasurementState = Meas_State_Idle;
		break;
	case Temp_State_Init:
		break;
	case Temp_State_Heat:
		break;
	case Temp_State_Settle:
		break;
	case Temp_State_Measure:
		break;
	case Temp_State_Deinit:
		break;
	default:
		break;
	}

	// Data logging loop
	if (FlagMeasurementState){
		if ((ADC_TotalBlocks>0) && (Log_WrittenBlocks < ADC_TotalBlocks) && (FlagMeasurementState < Meas_State_CloseLog) ){
			LD2_GPIO_Port->BSRR = LD2_Pin;
			LL_GPIO_SetOutputPin(DBG_IO3_GPIO_Port, DBG_IO3_Pin);
			LL_GPIO_ResetOutputPin(DBG_IO4_GPIO_Port, DBG_IO4_Pin);

			ADC_BufferReadBlock = Log_WrittenBlocks % ADC_BFR_BLOCKS;	// Calculate the virtual Block number
			if((Log_WrittenBlocks + ADC_BFR_BLOCKS) < ADC_TotalBlocks ){
				//ErrorResponse(ERRC_SYSTEM_ERROR, ERST_ADC_BUFFER_OVERRUN);
			}

			if(WriteBlockToFile(ADC_BufferReadBlock,Log_WrittenBlocks)){
				Log_WrittenBlocks++;
			}
			else{
				ADC_TotalBlocks--;	// Some botch to fix the mysterious behaviour of 100 samples offset
				LL_GPIO_SetOutputPin(DBG_IO4_GPIO_Port, DBG_IO4_Pin);
			}

			LL_GPIO_ResetOutputPin(DBG_IO3_GPIO_Port, DBG_IO3_Pin);

			LD2_GPIO_Port->BRR = LD2_Pin;
		}

		if(GetTick() > NextOutput){		// Measurement is running
			if(OperatingMode == Mode_Normal){
				WriteTemperaturesToFile();
			}

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
		UART_printf("#M;%d;%d;%d;%d;",FlagMeasurementState,ADC_PGA_Setting[(ADC_TotalBlocks)% ADC_BFR_BLOCKS],adc_val.ADC_Val[0],adc_val.ADC_Val[1]);

		adc_val.ADC_Reg = ADC_Buffer34[(uint16_t)ADC_BFR_idx];
		UART_printf("%d;%d",adc_val.ADC_Val[0],adc_val.ADC_Val[1]);

		for(uint8_t TKidx =0; TKidx<MAX6675_DEVICES;TKidx++)
		{
			UART_printf(";%.2f",Temp_TypeK[TKidx]);
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
		LL_GPIO_SetOutputPin(DBG_IO2_GPIO_Port, DBG_IO2_Pin);
		// format every sample into a line and print it onto the SD card. (single utoa's are ~50% faster than one sprintf)
		LFS_ret = LFS_WRITE_STRING(&littlefs, &file, "#B;");	// Block Number

		utoa(TotalWrittenBlocks,LogWriteBfr,10);
		LFS_ret = LFS_WRITE_STRING(&littlefs, &file, LogWriteBfr);

		LFS_ret = LFS_WRITE_STRING(&littlefs, &file, ";\n");
		LFS_ret = LFS_WRITE_STRING(&littlefs, &file, "#P;");	// PGA Setting

		utoa(ADC_PGA_Setting[ReadBlock],LogWriteBfr,10);
		LFS_ret = LFS_WRITE_STRING(&littlefs, &file, LogWriteBfr);
		LFS_ret = LFS_WRITE_STRING(&littlefs, &file, ";\n");

		union ADC_conv ADC_RegVal;
		for(ADC_Idx = Block_Start; ADC_Idx < Block_End; ADC_Idx++){

			ADC_RegVal.ADC_Reg = ADC_Buffer12[ADC_Idx];

			utoa(ADC_RegVal.ADC_Val[0],LogWriteBfr,10);
			LFS_ret = LFS_WRITE_STRING(&littlefs, &file, LogWriteBfr);
			LFS_ret = LFS_WRITE_STRING(&littlefs, &file, ";");
			utoa(ADC_RegVal.ADC_Val[1],LogWriteBfr,10);
			LFS_ret = LFS_WRITE_STRING(&littlefs, &file, LogWriteBfr);

			LFS_ret = LFS_WRITE_STRING(&littlefs, &file, ";");

			ADC_RegVal.ADC_Reg = ADC_Buffer34[ADC_Idx];

			utoa(ADC_RegVal.ADC_Val[0],LogWriteBfr,10);
			LFS_ret = LFS_WRITE_STRING(&littlefs, &file, LogWriteBfr);
			LFS_ret = LFS_WRITE_STRING(&littlefs, &file, ";");
			utoa(ADC_RegVal.ADC_Val[1],LogWriteBfr,10);
			LFS_ret = LFS_WRITE_STRING(&littlefs, &file, LogWriteBfr);
			LFS_ret = LFS_WRITE_STRING(&littlefs, &file, ";\n");
		}
		if(LFS_ret <0){
			GlobalWriteErrorFlag =1;
		}
		LL_GPIO_ResetOutputPin(DBG_IO2_GPIO_Port, DBG_IO2_Pin);
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

	EvalLFSError(LFS_WRITE_STRING(&littlefs, &file, "#T;"));	// Thermocouples
	for(uint8_t TKidx =0; TKidx<MAX6675_DEVICES;TKidx++)
	{
		//utoa(Temp_TypeK[TKidx],LogWriteBfr,10);
		sprintf(LogWriteBfr,"%.2f",Temp_TypeK[TKidx]);
		EvalLFSError(LFS_WRITE_STRING(&littlefs, &file, LogWriteBfr));
		EvalLFSError(LFS_WRITE_STRING(&littlefs, &file, ";"));
	}
	EvalLFSError(LFS_WRITE_STRING(&littlefs, &file, "\n"));

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


uint32_t MeasurementMemoryPrediction(void){

	uint32_t MemBytes = 1050+80; //Initially there should be around 270 bytes for the file header and 80 bytes for the footer

	uint32_t MeasureTime = SamplingTiming.PreHeatingTime + SamplingTiming.HeatingTime + SamplingTiming.CoolingTime;	// all values in ms

	uint32_t TotalTempSamples = MeasureTime / MEASURE_DATA_UPDATE_TIME;	// Calculate the approximate number of temperature samples
	DBG_LVL1("Temp Samples %d\n",TotalTempSamples);

	uint32_t TempMeasBytes = (TotalTempSamples * 29);		// Add the number of bytes for temperature measurement. Each line holds up to 21bytes
	MemBytes += TempMeasBytes;
	DBG_LVL1("Temperature Measure Bytes %d\n",TempMeasBytes);

	uint32_t SampleTimeSlow = (SamplingTiming.FastSampleTime <<SamplingTiming.MaxTimeMultiplier)/8000;
	DBG_LVL1("Slow sample time %d ms\n",SampleTimeSlow);

	uint32_t BytesPerBlock = (19 * ADC_BFR_SIZE)  +14;		// assuming 19 bytes per line + 14bytes for the block header
	DBG_LVL1("Bytes per Block  %d\n",BytesPerBlock);

	uint32_t TotalBlocks = MeasureTime/(SampleTimeSlow * ADC_BFR_SIZE);	// Calculate the total estimated number of blocks
	DBG_LVL1("Total Blocks %d\n",TotalBlocks);

	MemBytes += BytesPerBlock * TotalBlocks;	// Assuming the lowest sample rate this is the number of bytes over the whole measurement duration
	DBG_LVL1("Bytes in Blocks %d\n",BytesPerBlock * (TotalBlocks + ADC_MAX_MULTIPLIER));

	DBG_LVL1("Total bytes required %d\n",MemBytes);

	return MemBytes;
}

uint8_t CheckMemoryFileFit(void){
	uint32_t UsedMem=0;
	lfs_mem_size(&littlefs, "/", &UsedMem);

	uint32_t FreeMem = (w25qxx.block_count * w25qxx.block_size) - UsedMem;
	DBG_LVL1("Remaining Free Memory %lu\n",FreeMem);

	uint32_t NeededMem = MeasurementMemoryPrediction();

	if(FreeMem > NeededMem){
		DBG_LVL1("File fits into memory\n");
		return 1;
	}
	DBG_LVL1("File does not fit into memory!\n");
	return 0;
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
