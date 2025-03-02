/*
 * SCPI_server.cpp
 *
 *  Created on: Jun 29, 2022
 *      Author: wtronics
 */


#include <SCPI_server.h>
#include "dev_cal.h"
#include "ad56x4.h"

SCPI_Parser my_instrument;




/**************************************************************************/
/*!
  * @brief Initialize SCPI Server
  * @param None
  * @retval None
*/
void Init_SCPI_server(void){

	my_instrument.comm_mode = CommMode_SCPI;
	my_instrument.RegisterCommand("*IDN?", &Identify);
	my_instrument.RegisterCommand("*RST", &SystemReset);
	my_instrument.RegisterCommand("*ESR?", &SystemErrorStatus);
	my_instrument.RegisterCommand("*STB?", &SystemStatus);
	my_instrument.SetCommandTreeBase("MEMory:");
		my_instrument.RegisterCommand(":READfile", &Read_FileFromFlash);
		my_instrument.RegisterCommand(":WRITEtest", &Write_TestfileToFlash);
		my_instrument.RegisterCommand(":DIRectory", &Read_Directory);
		my_instrument.RegisterCommand(":DELete", &Delete_FileFromFlash);
		my_instrument.RegisterCommand(":UPLoad", &Set_FileUploadMode);

	my_instrument.SetCommandTreeBase("MEASure:");
		my_instrument.RegisterCommand(":TIMe:PREheating", &SetTiming);
		my_instrument.RegisterCommand(":TIMe:PREheating?", &GetTiming);
		my_instrument.RegisterCommand(":TIMe:HEATing", &SetTiming);
		my_instrument.RegisterCommand(":TIMe:HEATing?", &GetTiming);
		my_instrument.RegisterCommand(":TIMe:COOLing", &SetTiming);
		my_instrument.RegisterCommand(":TIMe:COOLing?", &GetTiming);
		my_instrument.RegisterCommand(":TIMe?", &GetTiming);
		my_instrument.RegisterCommand(":START", &SetMeasure);
		my_instrument.RegisterCommand(":STOP", &SetMeasure);
		my_instrument.RegisterCommand(":DUT", &SetDUT);
		my_instrument.RegisterCommand(":CHDESCription", &SetChannelDescription);
		my_instrument.RegisterCommand(":SET", &Set_AnalogValues);
	my_instrument.SetCommandTreeBase("SYSTem:");
		my_instrument.RegisterCommand(":MODE", &SetMode);
		my_instrument.RegisterCommand(":RATE", &SetCalSampleRate);
		my_instrument.RegisterCommand(":GAIN", &SetGain);
		my_instrument.RegisterCommand(":GAIN?", &GetGain);
		my_instrument.RegisterCommand(":CAL", &SetCalValue);
		my_instrument.RegisterCommand(":CAL?", &GetCalValues);
		my_instrument.RegisterCommand(":SAVE", &SaveCalValues);
		my_instrument.RegisterCommand(":PSUenable", &SetPSUEnable);
		my_instrument.RegisterCommand(":PSUenable?", &GetPSUEnable);
		my_instrument.RegisterCommand(":POWERstage", &SetPWSTGEnable);
		my_instrument.RegisterCommand(":POWERstage?",&GetPWSTGEnable);
		my_instrument.RegisterCommand(":GDPOWer", &SetGD_PowerEnable);
		my_instrument.RegisterCommand(":GDPOWer?",&GetGD_PowerEnable);
		my_instrument.RegisterCommand(":PWUVlo?", &GetPWSTGUVLO);
		my_instrument.RegisterCommand(":CLOCK?",&GetSystemTime);
		my_instrument.RegisterCommand(":CLOCK", &SetSystemTime);

}



/**
  * @brief Identify Device. Syntax: *IDN?
  * @param None
  * @retval None
  */
void Identify(SCPI_C commands, SCPI_P parameters, USART_TypeDef *huart) {
	UART_printf(UTTA_OWNER ", uTTA, SN" UTTA_SERIAL_NO ", " UTTA_SW_VERSION ", %s, %s\n",__DATE__,__TIME__);
}

/**
  * @brief Performs an system reset of uTTA
  * @param None
  * @retval None
  */
void SystemReset(SCPI_C commands, SCPI_P parameters, USART_TypeDef *huart){
	NVIC_SystemReset();
	while(1)
	{
	}
}


void SystemErrorStatus(SCPI_C commands, SCPI_P parameters, USART_TypeDef *huart){
	ErrorsOutput();
}


void SystemStatus(SCPI_C commands, SCPI_P parameters, USART_TypeDef *huart){
	uint16_t SystStatus=0;

	SystStatus = ((uint16_t)FlagMeasurementState) | (((uint16_t)ErrorTotalCount)<<8);
	UART_printf("SYST:STAT %04x\n",SystStatus);
}
/**
  * @brief Read a file from the FLASH memory.
  * This can ONLY be done while the system is in IDLE mode (no measurement running)
  * Syntax: MEMory:READfile FileName.FileExt
  * @param None
  * @retval None
  */
void Read_FileFromFlash(SCPI_C commands, SCPI_P parameters, USART_TypeDef *huart){
	char *first_parameter;
	const int BuffSize = 65;
	char Flash_readbuff[BuffSize];
	uint32_t LnCounter = 0;
	int LFS_ret = 0;
	uint32_t StartTime;
	uint32_t EndTime;

	if (parameters.Size() < 1) {
		ErrorResponse(ERRC_COMMAND_ERROR, ERST_TOO_FEW_PARAM);
		return;
	}

	if(FlagMeasurementState){	// check if system is Idle
		ErrorResponse(ERRC_ACCESS_ERROR, ERST_MEAS_RUNNING + FlagMeasurementState);
		return;
	}

	first_parameter = parameters.First();

	LFS_ret = lfs_file_open(&littlefs, &file, first_parameter, LFS_O_RDONLY);
	if( LFS_ret > 0){
		ErrorResponse(ERRC_SYSTEM_ERROR, ERST_FILE_NOT_FOUND);
		return;
	}
	UART_printf("Opened %s\n",first_parameter);
	StartTime = GetTick();

	do{
		LFS_ret = lfs_file_read(&littlefs, &file, &Flash_readbuff, BuffSize-1);

		if(LFS_ret > 0){
			//UART_printf("Read %d characters\r\n",LFS_ret);
			Flash_readbuff[LFS_ret] = 0;
			UART_printf("%s",Flash_readbuff);
		}


		LnCounter++;
	}while(LFS_ret > 0);

	EndTime = GetTick();

	UART_printf("\nRead took %i ms for %u Lines\n", EndTime-StartTime, LnCounter);

	// Close file
	LFS_ret = lfs_file_close(&littlefs, &file);
	if( LFS_ret < 0){
		ErrorResponse(ERRC_FILE_SYSTEM, (uint8_t)LFS_ret);
		return;
	}
}


/**
  * @brief Write a 1MB testfile to the FLASH memory and measure the time to check if the memory provides enough write speed for the job.
  * This can ONLY be done while the system is in IDLE mode (no measurement running)
  * Syntax: MEMory:WRITEtest
  * @param None
  * @retval None
  */
void Write_TestfileToFlash(SCPI_C commands, SCPI_P parameters, USART_TypeDef *huart){

	int LFS_ret = 0;
    uint32_t StartTime = 0;
    uint32_t EndTime = 0;

	if(FlagMeasurementState){	// check if system is Idle
		ErrorResponse(ERRC_ACCESS_ERROR, ERST_MEAS_RUNNING + FlagMeasurementState);
		return;
	}

	LFS_ret = lfs_file_open(&littlefs, &file, "Speedtest", LFS_O_WRONLY | LFS_O_CREAT | LFS_O_TRUNC);
	if( LFS_ret < 0){
		ErrorResponse(ERRC_SYSTEM_ERROR, ERST_FILE_NOT_FOUND);
		return;
	}

	UART_printf("Starting Write Test\n");
	StartTime = GetTick();
	/* Writing text */
	for(uint16_t LpIdx= 0; LpIdx <25000; LpIdx++){
		LFS_ret = LFS_WRITE_STRING(&littlefs, &file, "AbCdEfGhIjKlMnOpQrStUvWxYz0123456789{!}\n");
	}
	EndTime = GetTick();
	UART_printf("Ended Write Test\nWrite took %i ms\n", EndTime-StartTime);

	/* Close file */
	LFS_ret = lfs_file_close(&littlefs, &file);

	if( LFS_ret < 0)
		ErrorResponse(ERRC_FILE_SYSTEM, (uint8_t)LFS_ret);

}

/**
  * @brief Reads a directory from the FLASH memory and puts it on serial port. Use parameter "ALL" for detailed file info.
  * This can ONLY be done while the system is in IDLE mode (no measurement running)
  * Syntax: MEMory:DIRectory Directory[,ALL]
  * @param None
  * @retval None
  */
void Read_Directory(SCPI_C commands, SCPI_P parameters, USART_TypeDef *huart){


    int res = 0;

    if (parameters.Size() < 1) {
		ErrorResponse(ERRC_COMMAND_ERROR, ERST_TOO_FEW_PARAM);
		return;
    }

	if(FlagMeasurementState){	// check if system is Idle
		ErrorResponse(ERRC_ACCESS_ERROR, ERST_MEAS_RUNNING + FlagMeasurementState);
		return;
	}

	if (parameters.Size() >1){
		parameters.toUpperCase(parameters[1]);
		if((strcmp(parameters[1],"ALL")==0)){
		}
	}
	//char first_parameter[20] = "/";
	//strcat(first_parameter, parameters[0]);
	//UART_printf("Reading: %s\n", parameters[0]);
	lfs_ls(&littlefs, parameters[0]);

    if (res){
    	ErrorResponse(ERRC_FILE_SYSTEM,(uint8_t)res);
    }else{
    	UART_printf("#END\n");
    }
}

/**
  * @brief Deletes a file from the FLASH memory
  * This can ONLY be done while the system is in IDLE mode (no measurement running)
  * Syntax: MEMory:DELete [File]
  * @param None
  * @retval None
  */
void Delete_FileFromFlash(SCPI_C commands, SCPI_P parameters, USART_TypeDef *huart){

    int res = 0;

    if (parameters.Size() < 1) {
		ErrorResponse(ERRC_COMMAND_ERROR, ERST_TOO_FEW_PARAM);
		return;
    }

	if(FlagMeasurementState){	// check if system is Idle
		ErrorResponse(ERRC_ACCESS_ERROR, ERST_MEAS_RUNNING + FlagMeasurementState);
		return;
	}
	//UART_printf("Deleting: %s\n",parameters[0]);
    res = lfs_remove(&littlefs, parameters[0]);

    if (res){
    	ErrorResponse(ERRC_FILE_SYSTEM,(uint8_t)res);
    }else{
    	UART_printf("Deleted: %s\n",parameters[0]);
    }
}


void Set_FileUploadMode(SCPI_C commands, SCPI_P parameters, USART_TypeDef *huart){

    int LFS_ret = 0;
    int FnameLen = 0;

    if (parameters.Size() != 1) {
		ErrorResponse(ERRC_COMMAND_ERROR, ERST_TOO_FEW_PARAM);
		return;
    }

	if(FlagMeasurementState){	// check if system is Idle
		ErrorResponse(ERRC_ACCESS_ERROR, ERST_MEAS_RUNNING + FlagMeasurementState);
		return;
	}
	FnameLen = strlen(parameters[0]);
	if((FnameLen < 3)||(FnameLen > 14)){
		ErrorResponse(ERRC_COMMAND_ERROR, ERST_PARAM_TOO_LONG);
		return;
	}

	UART_printf("Entering File upload Mode for File: %s\n",parameters[0]);

	LFS_ret = lfs_file_open(&littlefs, &file, parameters[0], LFS_O_WRONLY | LFS_O_CREAT | LFS_O_TRUNC);
	if( LFS_ret > 0){
		ErrorResponse(ERRC_SYSTEM_ERROR, ERST_FILE_NOT_FOUND);
		return;
	}
	my_instrument.comm_mode=CommMode_Text;
}


void FileUpload_SerialToFile(char* message){
	const char* eof_chars = "<EOF>";
	int LFS_ret = 0;
	char FileWriteBuff[65];

	strcpy(FileWriteBuff , message);

	char *TermCharIdx = strstr(FileWriteBuff, eof_chars);
	if (TermCharIdx != NULL) {
		//Received the end of file marker
		LFS_ret = lfs_file_close(&littlefs, &file);
		if( LFS_ret > 0){
			ErrorResponse(ERRC_SYSTEM_ERROR, LFS_ret);
			return;
		}
		UART_printf("Received end of file flag, closing file!\n");
		my_instrument.comm_mode = CommMode_SCPI;
	}else{


		UART_printf("Writing: %s\n", FileWriteBuff);
		LFS_ret = LFS_WRITE_STRING(&littlefs, &file, FileWriteBuff);
		LFS_ret = LFS_WRITE_STRING(&littlefs, &file, "\n");
	}

	return;
}

/**
  * @brief Sets the sampling timing for the next measurement.
  * This can ONLY be done while the system is in IDLE mode (no measurement running)
  * Syntax: MEASure:PREheating x		x = PreHeating Time in ms, Range 30s to 3600s
  * Syntax: MEASure:HEATing x			x = Heating Time in ms, Range 10s to 10800s (3hours)
  * Syntax: MEASure:COOLing x			x = Cooling Time in ms, Range 60s to 21600s (6hours)
  * @param None
  * @retval None
  */
void SetTiming(SCPI_C commands, SCPI_P parameters, USART_TypeDef *huart){
	char *first_parameter;
	char *last_header;
	uint32_t Rcv_Param =0;

	if (parameters.Size() < 1) {
		ErrorResponse(ERRC_COMMAND_ERROR, ERST_TOO_FEW_PARAM);
		return;
	}

	if(FlagMeasurementState){	// check if system is Idle
		ErrorResponse(ERRC_ACCESS_ERROR, ERST_MEAS_RUNNING + FlagMeasurementState);
		return;
	}

	last_header = commands.Last();
	parameters.toUpperCase(last_header);
	first_parameter = parameters.First();

	Rcv_Param = (uint32_t)atol(first_parameter);

	if((strcmp(last_header,"PRE")==0)||(strcmp(last_header,"PREHEATING")==0)){
		if((Rcv_Param <= MEAS_MAX_PREHEATING_TIME) && (Rcv_Param >= MEAS_MIN_PREHEATING_TIME)){
			SamplingTiming.PreHeatingTime = Rcv_Param;
		}
	}
	else if((strcmp(last_header,"HEAT")==0)||(strcmp(last_header,"HEATING")==0)){
		if(((Rcv_Param <= MEAS_MAX_HEATING_TIME) && (Rcv_Param >= MEAS_MIN_HEATING_TIME))||(Rcv_Param == 0)){
			SamplingTiming.HeatingTime = Rcv_Param;
		}
	}
	else if((strcmp(last_header,"COOL")==0)||(strcmp(last_header,"COOLING")==0)){
		if((Rcv_Param <= MEAS_MAX_COOLING_TIME) && (Rcv_Param >= MEAS_MIN_COOLING_TIME)){
			SamplingTiming.CoolingTime = Rcv_Param;
		}
	}
	else{
		ErrorResponse(ERRC_COMMAND_ERROR, ERST_UNKNOWN_COMMAND);
		return;
	}
	UART_printf("MEAS:TIM %u;%u;%u\n", SamplingTiming.PreHeatingTime,SamplingTiming.HeatingTime, SamplingTiming.CoolingTime);
	//MeasurementMemoryPrediction();
}

/**
  * @brief Returns the sampling timing for the next measurement.
  * Syntax: MEASure:TIMe:PREheating?	Returns the PreHeating time in ms
  * Syntax: MEASure:TIMe:HEATing?		Returns the Heating time in ms
  * Syntax: MEASure:TIMe:COOLing?		Returns the Cooling time in ms
  * Syntax: MEASure:TIMe?				Returns the all 3 times in ms. Format: N;O;P\n : N = PreHeating time in ms, O = Heating time in ms, P = Cooling Time in ms
  * @param None
  * @retval None
  */
void GetTiming(SCPI_C commands, SCPI_P parameters, USART_TypeDef *huart){
	char *last_header;

	if (parameters.Size() < 1) {
		UART_printf("%u;%u;%u\n", SamplingTiming.PreHeatingTime,SamplingTiming.HeatingTime, SamplingTiming.CoolingTime);
		return;
	}

	last_header = commands.Last();
	parameters.toUpperCase(last_header);

	if((strcmp(last_header,"PRE?")==0)||(strcmp(last_header,"PREHEATING?")==0)){
		UART_printf("MEAS:TIM %u\n", SamplingTiming.PreHeatingTime);
	}
	else if((strcmp(last_header,"HEAT?")==0)||(strcmp(last_header,"HEATING?")==0)){
		UART_printf("MEAS:TIM %u\n", SamplingTiming.HeatingTime);
	}
	else if((strcmp(last_header,"COOL?")==0)||(strcmp(last_header,"COOLING?")==0)){
		UART_printf("MEAS:TIM %u\n", SamplingTiming.CoolingTime);
	}
	else{
		ErrorResponse(ERRC_COMMAND_ERROR, ERST_UNKNOWN_COMMAND);
	}
}

/**
  * @brief Starts and stops the measurement
  * Syntax: MEASure:START		Starts the measurement
  * Syntax: MEASure:STOP		Stops the measurement
  * @param None
  * @retval None
  */
void SetMeasure(SCPI_C commands, SCPI_P parameters, USART_TypeDef *huart){
	char *last_header;

	last_header = commands.Last();
	parameters.toUpperCase(last_header);

	if((strcmp(last_header,"START")==0)){
		if(FlagMeasurementState == Meas_State_Idle){
			if( OperatingMode == MODE_NORMAL){
				FlagMeasurementState = Meas_State_Init;
			}
			else{
				FlagMeasurementState = Cal_State_Init;
			}
			UART_printf("OK\n");
		}
		else{
			ErrorResponse(ERRC_ACCESS_ERROR, ERST_MEAS_RUNNING+FlagMeasurementState);
		}
	}
	else if((strcmp(last_header,"STOP")==0)){

		if(FlagMeasurementState != Meas_State_Idle){
			if( OperatingMode == MODE_NORMAL){
				FlagMeasurementState = Meas_State_Deinit;
			}
			else{
				FlagMeasurementState = Cal_State_DeInit;
			}
			//UART_printf("OK\n");
		}
		else{
			ErrorResponse(ERRC_ACCESS_ERROR, ERST_MEAS_RUNNING+FlagMeasurementState);
		}
	}
	else{
		ErrorResponse(ERRC_COMMAND_ERROR, ERST_UNKNOWN_COMMAND);
	}
}


/**
  * @brief Sets the name of the DUT which is also used as file name.
  * This can ONLY be done while the system is in IDLE mode (no measurement running)
  * Syntax: MEASure:DUT [aaaaaaaaaaa]		String of maximum 14 characters. Please don't use special characters
  * @param None
  * @retval None
  */
void SetDUT(SCPI_C commands, SCPI_P parameters, USART_TypeDef *huart){
	char *first_parameter;
	int FTest;
	char FilNam[MAX_DUT_NAME_LENGTH];//={''};

	if (parameters.Size() < 1) {
		ErrorResponse(ERRC_COMMAND_ERROR, ERST_TOO_FEW_PARAM);
		return;
	}

	if(FlagMeasurementState){	// check if system is Idle
		ErrorResponse(ERRC_ACCESS_ERROR, ERST_MEAS_RUNNING + FlagMeasurementState);
		return;
	}

	first_parameter = parameters.First();

	if(strlen(first_parameter)>14 ){
		ErrorResponse(ERRC_COMMAND_ERROR, ERST_PARAM_TOO_LONG);
		return;
	}

	sprintf(FilNam,"%s.umf",first_parameter);

	lfs_info FilInfo;
	FTest = lfs_stat(&littlefs,FilNam,&FilInfo);
	if(FTest < 0){
		strcpy(DUT_Name,FilNam);
		UART_printf("OK %s\n", FilNam);
	}
	else{
		ErrorResponse(ERRC_SYSTEM_ERROR, ERST_FILE_EXISTS);
	}
}

/**
  * @brief Sets the symbolic name for each ADC channel and the scaling factors for post processing
  * This can ONLY be done while the system is in IDLE mode (no measurement running)
  * Syntax: MEASure:CHDESCription N,[aaaaa],O,P,Q		N       = Number of the channel (1 to 3),
  * 													[aaaaa] = Name of the channel in the Log-File,
  * 													O       = Offset for scaling in uV,
  * 													P       = Linear Gain in uV/K,
  * 													Q       = Quadratic Gain in uV/K^2
  * @param None
  * @retval None
  */
void SetChannelDescription(SCPI_C commands, SCPI_P parameters, USART_TypeDef *huart){

	char *first_parameter;
	uint8_t ChNo=0;

	if (parameters.Size() < 5) {
		ErrorResponse(ERRC_COMMAND_ERROR, ERST_TOO_FEW_PARAM);
		return;
	}

	if(FlagMeasurementState){	// check if system is Idle
		ErrorResponse(ERRC_ACCESS_ERROR, ERST_MEAS_RUNNING + FlagMeasurementState);
		return;
	}

	first_parameter = parameters.First();
	ChNo = (uint8_t)atol(first_parameter)-1;

	if((ChNo < 4) && (ChNo >= 0)){
		if(strlen(parameters[1])<15){
			strcpy(Channels[ChNo].CH_Name ,parameters[1]);
		}else{
			strncpy(Channels[ChNo].CH_Name, parameters[1], 14);
		}

		float Param = 0.0;
		Param = atof(parameters[2]);
		if(Param > -1000000.0 && Param < 1000000.0)		// Boundary for Offset: +/-1V
			Channels[ChNo].CH_Offs = Param;

		Param = atof(parameters[3]);
		if(Param > -100000.0 && Param < 100000.0)		// Boundary for Linear Gain: +/-100mV/K
			Channels[ChNo].CH_LinGain = Param;

		Param = atof(parameters[4]);
		if(Param > -10000.0 && Param < 10000.0)			// Boundary for Quadratic Gain: +/-10mV/K
			Channels[ChNo].CH_QuadGain = Param;

		UART_printf("#CH %d;%s;%f;%f;%f\n", ChNo+1, Channels[ChNo].CH_Name, Channels[ChNo].CH_Offs, Channels[ChNo].CH_LinGain, Channels[ChNo].CH_QuadGain);
	}
	else{
		ErrorResponse(ERRC_COMMAND_ERROR, ERST_PARAM_OUT_OF_RANGE);
	}
}


/**
  * @brief Sets the analog values to the analog frontend
  * This can ONLY be done while the system is in IDLE mode (no measurement running)
  * Syntax: MEASure:SET ch, value			ch    = Name of the Channel [ISEN, VOFFS1, VOFFS2]
  * 										value = Floating point value of the set value, in Calibration Mode the input value is interpreted as DAC Value (Range: 0..65535)
  * @param None
  * @retval None
  */
void Set_AnalogValues(SCPI_C commands, SCPI_P parameters, USART_TypeDef *huart){
	char *first_parameter;

	if (parameters.Size() != 2) {
		ErrorResponse(ERRC_COMMAND_ERROR, ERST_TOO_FEW_PARAM);
		return;
	}

	if(FlagMeasurementState > Meas_State_Idle && FlagMeasurementState < Cal_State_Init){	// check if system is Idle or in Cal Mode
		ErrorResponse(ERRC_ACCESS_ERROR, ERST_MEAS_RUNNING + FlagMeasurementState);
		return;
	}

	first_parameter = parameters.First();
	parameters.toUpperCase(first_parameter);
	float SetValue = atof(parameters[1]);
	uint8_t ChNo = 0;

	if((strcmp(first_parameter,"ISEN")==0)){
		ChNo=0;
	}
	else if((strcmp(first_parameter,"VOFF0")==0)){
		ChNo=2;
	}
	else if((strcmp(first_parameter,"VOFF1")==0)){
		ChNo=3;
	}
	else{
		ErrorResponse(ERRC_COMMAND_ERROR, ERST_UNKNOWN_COMMAND);
		return;
	}

	int8_t DAC_ret = AD56x4_WriteChannelCalibrated((DAC_Ch_t)ChNo, SetValue);
	UART_printf("OK %d\n", DAC_ret);
}



/**
  * @brief Changes the measurement mode between Normal Mode and Calibration Mode
  * This can ONLY be done while the system is in IDLE mode (no measurement running)
  * Syntax: SYSTem:MODE NORMAL		Set the system in NORMAL mode (default after power on)
  * Syntax: SYSTem:MODE CAL			Set the system in CALIBRATION mode
  * @param None
  * @retval None
  */
void SetMode(SCPI_C commands, SCPI_P parameters, USART_TypeDef *huart){
	char *first_parameter;

	if (parameters.Size() < 1) {
		ErrorResponse(ERRC_COMMAND_ERROR, ERST_TOO_FEW_PARAM);
		return;
	}

	if(FlagMeasurementState){	// check if system is Idle
		ErrorResponse(ERRC_ACCESS_ERROR, ERST_MEAS_RUNNING + FlagMeasurementState);
		return;
	}

	first_parameter = parameters.First();
	parameters.toUpperCase(first_parameter);

	if((strcmp(first_parameter,"NORMAL")==0)){
		OperatingMode = MODE_NORMAL;
		UART_printf("OK\n");
	}
	else if((strcmp(first_parameter,"CAL")==0)){
		OperatingMode = MODE_CALIBRATION;
		UART_printf("OK\n");
	}
	else{
		ErrorResponse(ERRC_COMMAND_ERROR, ERST_UNKNOWN_COMMAND);
	}
}


/**
  * @brief Control of the external power supply.
  * This can ONLY be done while the system is in CALIBRATION mode
  * Syntax: SYSTem:PSUenable [HIGH/LOW/ON/OFF/0/1]
  * @param None
  * @retval None
  */
void SetPSUEnable(SCPI_C commands, SCPI_P parameters, USART_TypeDef *huart){
	  //Valid states are : "HIGH", "LOW", "ON", "OFF", "1" and "0"
	  //and any lowercase/uppercase combinations

	char *first_parameter;
	int8_t State;
	if (parameters.Size() != 1) {
		ErrorResponse(ERRC_COMMAND_ERROR, ERST_TOO_FEW_PARAM);
		return;
	}

	if(OperatingMode != MODE_CALIBRATION){
		ErrorResponse(ERRC_ACCESS_ERROR, ERST_NOT_ALLOWED_IN_MODE);
		return;
	}

	first_parameter = parameters.First();
	State = parameters.evalBoolParam(first_parameter);

	if (State >=0) {
		(State & 0x01) ? LL_GPIO_SetOutputPin(PSU_EN_DO_GPIO_Port, PSU_EN_DO_Pin) : LL_GPIO_ResetOutputPin(PSU_EN_DO_GPIO_Port, PSU_EN_DO_Pin);
		UART_printf("#PSU %d\n", State);
	} else {
		ErrorResponse(ERRC_COMMAND_ERROR,ERST_PARAM_OUT_OF_RANGE);
	}
}


/**
  * @brief Return the current enable status of the external power supply.
  * Syntax: SYSTem:PSUenable?
  * @param None
  * @retval None
  */


void GetPSUEnable(SCPI_C commands, SCPI_P parameters, USART_TypeDef *huart){

	UART_printf("#PSU %d\n",LL_GPIO_ReadInputPort(PSU_EN_DO_GPIO_Port) & PSU_EN_DO_Pin);
}


/**
  * @brief Control of the power stage for switching power to the DUT.
  * This can ONLY be done while the system is in CALIBRATION mode
  * Syntax: SYSTem:POWERstage [HIGH/LOW/ON/OFF/0/1]
  * @param None
  * @retval None
  */
void SetPWSTGEnable(SCPI_C commands, SCPI_P parameters, USART_TypeDef *huart){
	  //Valid states are : "HIGH", "LOW", "ON", "OFF", "1" and "0"
	  //and any lowercase/uppercase combinations

	char *first_parameter;
	int8_t State;
	if (parameters.Size() < 1) {
		ErrorResponse(ERRC_COMMAND_ERROR, ERST_TOO_FEW_PARAM);
		return;
	}

	if(OperatingMode != MODE_CALIBRATION){
		ErrorResponse(ERRC_ACCESS_ERROR, ERST_NOT_ALLOWED_IN_MODE);
		return;
	}
	first_parameter = parameters.First();
	State = parameters.evalBoolParam(first_parameter);

	if (State >=0) {
		(State & 0x01) ? LL_GPIO_SetOutputPin(PWSTG_EN_DO_GPIO_Port, PWSTG_EN_DO_Pin) : LL_GPIO_ResetOutputPin(PWSTG_EN_DO_GPIO_Port, PWSTG_EN_DO_Pin);
		UART_printf("#PWSTG %d\n", State);
		//HAL_GPIO_WritePin(PWSTG_EN_DO_GPIO_Port, PWSTG_EN_DO_Pin, (GPIO_PinState)State);
		//UART_printf("%d\n", State);
	} else {
		ErrorResponse(ERRC_COMMAND_ERROR,ERST_PARAM_OUT_OF_RANGE);
	}
}


/**
  * @brief Return the status of the power stage for switching power to the DUT.
  * Syntax: SYSTem:POWERstage?
  * @param None
  * @retval None
  */
void GetPWSTGEnable(SCPI_C commands, SCPI_P parameters, USART_TypeDef *huart){

	UART_printf("#PWSTG %d\n",LL_GPIO_ReadInputPort(PWSTG_EN_DO_GPIO_Port) & PWSTG_EN_DO_Pin);
}

/**
  * @brief Control the power supply of the power stage.
  * This can ONLY be done while the system is in CALIBRATION mode
  * Syntax: SYSTem:GDPOWer [HIGH/LOW/ON/OFF/0/1]
  * @param None
  * @retval None
  */
void SetGD_PowerEnable(SCPI_C commands, SCPI_P parameters, USART_TypeDef *huart){
	  //Valid states are : "HIGH", "LOW", "ON", "OFF", "1" and "0"
	  //and any lowercase/uppercase combinations

	char *first_parameter;
	int8_t State;
	if (parameters.Size() < 1) {
		ErrorResponse(ERRC_COMMAND_ERROR, ERST_TOO_FEW_PARAM);
		return;
	}

	if(OperatingMode != MODE_CALIBRATION){
		ErrorResponse(ERRC_ACCESS_ERROR, ERST_NOT_ALLOWED_IN_MODE);
		return;
	}
	first_parameter = parameters.First();
	State = parameters.evalBoolParam(first_parameter);

	if (State >=0) {
		(State & 0x01) ? LL_GPIO_SetOutputPin(PWSTG_PWR_EN_DO_GPIO_Port, PWSTG_PWR_EN_DO_Pin) : LL_GPIO_ResetOutputPin(PWSTG_PWR_EN_DO_GPIO_Port, PWSTG_PWR_EN_DO_Pin);
		UART_printf("#GD %d\n", State);
		//HAL_GPIO_WritePin(PWSTG_PWR_EN_DO_GPIO_Port, PWSTG_PWR_EN_DO_Pin, (GPIO_PinState)State);
		//UART_printf("%d\n", State);
	} else {
		ErrorResponse(ERRC_COMMAND_ERROR,ERST_PARAM_OUT_OF_RANGE);
	}
}

/**
  * @brief Return the status of the power supply of the power stage.
  * Syntax: SYSTem:GDPOWer?
  * @param None
  * @retval None
  */
void GetGD_PowerEnable(SCPI_C commands, SCPI_P parameters, USART_TypeDef *huart){
	UART_printf("#GD %d\n",LL_GPIO_ReadInputPort(PWSTG_PWR_EN_DO_GPIO_Port) & PWSTG_PWR_EN_DO_Pin);
}


/**
  * @brief Return the undervoltage status of the Gatedriver Battery
  * Syntax: SYSTem:PWUVlo?
  * @param None
  * @retval None
  */
void GetPWSTGUVLO(SCPI_C commands, SCPI_P parameters, USART_TypeDef *huart){

	UART_printf("#UVLO %d\n",LL_GPIO_ReadInputPort(PWSTG_UVLO_DI_GPIO_Port) & PWSTG_UVLO_DI_Pin);
}


/**
  * @brief Sets the sample rate for calibration mode. This only influences the sample rate on the serial port. Logging to memory is still performed with the slowest ADC setting.
  * This can ONLY be done while the system is in IDLE mode (no measurement running)
  * Syntax: SYSTem:RATE x		x = Calibration sample rate in ms. Default: 250ms, Range: 25ms to 2500ms
  * @param None
  * @retval None
  */
void SetCalSampleRate(SCPI_C commands, SCPI_P parameters, USART_TypeDef *huart){

	char *first_parameter;
	uint32_t Rcv_Param =0;

	if (parameters.Size() < 1) {
		ErrorResponse(ERRC_COMMAND_ERROR, ERST_TOO_FEW_PARAM);
		return;
	}

	if(FlagMeasurementState){	// check if system is Idle
		ErrorResponse(ERRC_ACCESS_ERROR, ERST_MEAS_RUNNING + FlagMeasurementState);
		return;
	}

	first_parameter = parameters.First();
	Rcv_Param = (uint32_t)atol(first_parameter);

	if((Rcv_Param <= CAL_MAX_SAMPLE_TIME) && (Rcv_Param >= CAL_MIN_SAMPLE_TIME)){
		SamplingTiming.CalSampleTime = Rcv_Param;
		UART_printf("#CSR %d\n",SamplingTiming.CalSampleTime);
	}
	else{
		ErrorResponse(ERRC_COMMAND_ERROR, ERST_PARAM_OUT_OF_RANGE);
	}
}


/**
  * @brief Sets the PGA for the driver ADC channel for its various sampling modes
  * This can ONLY be done while the system is in IDLE mode (no measurement running)
  * Syntax: SYSTem:GAIN x				x = Sets the gain independant of any measurement mode. This is needed for calibration mode
  * Syntax: SYSTem:GAIN HEATing,x		x = Sets the gain for heating mode
  * Syntax: SYSTem:GAIN COOLing,x		x = Sets the gain for cooling and PreHeating mode
  * @param None
  * @retval None
  */
void SetGain(SCPI_C commands, SCPI_P parameters, USART_TypeDef *huart){

	char *first_parameter;
	uint32_t Rcv_Param =0;

	if (parameters.Size() < 1) {
		ErrorResponse(ERRC_COMMAND_ERROR, ERST_TOO_FEW_PARAM);
		return;
	}

	if(FlagMeasurementState > Meas_State_Idle && FlagMeasurementState < Cal_State_Init){	// check if system is Idle
		ErrorResponse(ERRC_ACCESS_ERROR, ERST_MEAS_RUNNING + FlagMeasurementState);
		return;
	}
	if(parameters.Size()==2){
		first_parameter = parameters.First();
		parameters.toUpperCase(first_parameter);
		Rcv_Param=atoi(parameters[1]);

		if((strcmp(first_parameter,"HEAT")==0)||(strcmp(first_parameter,"HEATING")==0)){
			if((Rcv_Param <= PGA_MAX_GAIN) && (Rcv_Param >= PGA_MIN_GAIN)){
				PGA_Gains.Heating = Rcv_Param;
			}
			else{
				ErrorResponse(ERRC_COMMAND_ERROR, ERST_PARAM_OUT_OF_RANGE);
				return;
			}
		}
		else if((strcmp(first_parameter,"COOL")==0)||(strcmp(first_parameter,"COOLING")==0)){
			if((Rcv_Param <= PGA_MAX_GAIN) && (Rcv_Param >= PGA_MIN_GAIN)){
				PGA_Gains.Cooling = Rcv_Param;
			}
			else{
				ErrorResponse(ERRC_COMMAND_ERROR, ERST_PARAM_OUT_OF_RANGE);
				return;
			}
		}
		else{
			ErrorResponse(ERRC_COMMAND_ERROR, ERST_UNKNOWN_COMMAND);
			return;
		}
	}
	else{
		first_parameter = parameters.First();
		Rcv_Param = (uint32_t)atol(first_parameter);

		if((Rcv_Param <= PGA_MAX_GAIN) && (Rcv_Param >= PGA_MIN_GAIN)){

			SetPGAGain((uint8_t)Rcv_Param);
		}
		else{
			ErrorResponse(ERRC_COMMAND_ERROR, ERST_PARAM_OUT_OF_RANGE);
			return;
		}
	}
	UART_printf("#PGA %d;%d;%d\n",PGA_Gains.Set,PGA_Gains.Cooling,PGA_Gains.Heating);
}


/**
  * @brief Sets the PGA directly on the GPIO
  * @param uint8_t Gain	Gain-Setting of the PGA from 0 to 3
  * @retval None
  */
void SetPGAGain(uint8_t Gain){

	(Gain & 0x01) ? LL_GPIO_SetOutputPin(GAIN_B0_DO_GPIO_Port, GAIN_B0_DO_Pin) : LL_GPIO_ResetOutputPin(GAIN_B0_DO_GPIO_Port, GAIN_B0_DO_Pin);
	(Gain & 0x02) ? LL_GPIO_SetOutputPin(GAIN_B1_DO_GPIO_Port, GAIN_B1_DO_Pin) : LL_GPIO_ResetOutputPin(GAIN_B1_DO_GPIO_Port, GAIN_B1_DO_Pin);

	PGA_Gains.Set = Gain;
}

/**
  * @brief Returns the PGA settings for the driver ADC channel for its various sampling modes
  * Syntax: SYSTem:GAIN?			Returns: A;B;C		A=Current gain setting, B = Cooling & PreHeating gain setting, C = Heating gain setting
  * @param None
  * @retval None
  */
void GetGain(SCPI_C commands, SCPI_P parameters, USART_TypeDef *huart){
	UART_printf("#PGA %d;%d;%d\n",PGA_Gains.Set,PGA_Gains.Cooling,PGA_Gains.Heating);
}

/**
  * @brief Set a single calibration value to the calibration memory
  * Syntax: SYSTem:CAL ch, offs, lingain, cubgain  	ch: 		Name of the channel the calibration value belongs to
  * 												offs:		Calibration offset value
  * 												lingain:	Calibration linear gain factor
  * 												cubgain:	Calibration cubic gain factor
  * @param None
  * @retval None
  */
void SetCalValue(SCPI_C commands, SCPI_P parameters, USART_TypeDef *huart){
	char *first_parameter;
	float Rcv_Param =0.0;


	if (parameters.Size() != 4) {
		ErrorResponse(ERRC_COMMAND_ERROR, ERST_TOO_FEW_PARAM);
		return;
	}

	if(FlagMeasurementState){	// check if system is Idle
		ErrorResponse(ERRC_ACCESS_ERROR, ERST_MEAS_RUNNING + FlagMeasurementState);
		return;
	}
	first_parameter = parameters.First();
	parameters.toUpperCase(first_parameter);
	uint8_t ParamIdx = 0;
	for (; ParamIdx < MaxCalChannels; ParamIdx++){
		if((strcmp(first_parameter,CalChannelNames[ParamIdx])==0)){
			break;
		}
	}

	if(ParamIdx >= MaxCalChannels){		// sanity checking to prevent further operations with an invalid parameter
		ErrorResponse(ERRC_COMMAND_ERROR, ERST_UNKNOWN_COMMAND);
		return;
	}
	Rcv_Param = atof(parameters[1]);
	ChannelCalibValues[ParamIdx].Offset = Rcv_Param;

	Rcv_Param = atof(parameters[2]);
	ChannelCalibValues[ParamIdx].LinGain = Rcv_Param;

	Rcv_Param = atof(parameters[3]);
	ChannelCalibValues[ParamIdx].CubGain = Rcv_Param;

	UART_printf("#CAL %s, %f, %f, %f\n",CalChannelNames[ParamIdx], ChannelCalibValues[ParamIdx].Offset, ChannelCalibValues[ParamIdx].LinGain, ChannelCalibValues[ParamIdx].CubGain);

}

/**
  * @brief Returns the whole calibration Information of the device
  * Syntax: SYSTem:CAL?
  * @param None
  * @retval None
  */
void GetCalValues(SCPI_C commands, SCPI_P parameters, USART_TypeDef *huart){
	Read_CalibrationFromFlash(&littlefs, &file, 1);
}


void SaveCalValues(SCPI_C commands, SCPI_P parameters, USART_TypeDef *huart){
	Write_CalibrationToFlash(&littlefs, &file);
}

/**
  * @brief Returns the uTTA system time via USART
  * Syntax: SYSTem:CLOCK?			Returns: DD.MM.YYYY hh:mm:ss\n
  * @param None
  * @retval None
  */
void GetSystemTime(SCPI_C commands, SCPI_P parameters, USART_TypeDef *huart){
	UART_printf("#TIME ");
	print_RTC_DateTime(0,0);
	UART_printf("\n");
}


/**
  * @brief Sets the uTTA system time via USART
  * This can ONLY be done while the system is in IDLE mode (no measurement running)
  * Syntax: SYSTem:CLOCK DATE,DD,MM,YYYY
  * Syntax: SYSTem:CLOCK TIME,HH,MM,SS
  * @param None
  * @retval None
  */
void SetSystemTime(SCPI_C commands, SCPI_P parameters, USART_TypeDef *huart){
	char *first_parameter;
	uint32_t Rcv_Param =0;
	RTC_DateTypeDef NewDate;
	RTC_TimeTypeDef NewTime;

	if (parameters.Size() < 1) {
		ErrorResponse(ERRC_COMMAND_ERROR, ERST_TOO_FEW_PARAM);
		return;
	}

	if(FlagMeasurementState){	// check if system is Idle
		ErrorResponse(ERRC_ACCESS_ERROR, ERST_MEAS_RUNNING + FlagMeasurementState);
		return;
	}
	if(parameters.Size()==4){		// Command contains Date or Time in format: DATE,TT,MM,YYYY   or TIME,hh,mm,ss
		first_parameter = parameters.First();
		parameters.toUpperCase(first_parameter);

		if((strcmp(first_parameter,"DATE")==0)){
			NewDate.RTC_Date = atoi(parameters[1]);
			NewDate.RTC_Month = atoi(parameters[2]);
			Rcv_Param = atoi(parameters[3]);
		    if(Rcv_Param>99){
		    	Rcv_Param-=2000;
		    }
			NewDate.RTC_Year = Rcv_Param;

			RTC_write_date_struct(&NewDate);
		}
		else if((strcmp(first_parameter,"TIME")==0)){
			NewTime.RTC_Hours = atoi(parameters[1]);
			NewTime.RTC_Minutes = atoi(parameters[2]);
			NewTime.RTC_Seconds = atoi(parameters[3]);

			RTC_write_time_struct(&NewTime);
		}
		else{
			ErrorResponse(ERRC_COMMAND_ERROR, ERST_UNKNOWN_COMMAND);
			return;
		}
	}
	else if(parameters.Size()==6){		// Command contains Date + Time in format: TT,MM,YYYY,hh,mm,ss
		//TODO: Date+Time setting to be implemented
	}
	else{
		//TODO: Error Handling to be implemented
	}
}


uint8_t MeasurementMemoryPrediction(void){

	uint32_t MemBytes = 1050+80; //Initially there should be around 270 bytes for the file header and 80 bytes for the footer

	uint32_t MeasureTime = 0;
	MeasureTime = SamplingTiming.PreHeatingTime + SamplingTiming.HeatingTime + SamplingTiming.CoolingTime;	// all values in ms

	uint32_t TotalTempSamples = 0;
	TotalTempSamples = MeasureTime / MEASURE_TEMP_UPDATE_TIME;	// Calculate the approximate number of temperature samples

	UART_printf("Samples %d\n",TotalTempSamples);
	MemBytes += (TotalTempSamples * 21);		// Add the number of bytes for temperature measurement. Each line holds up to 21bytes
	UART_printf("Temperature Measure Bytes %d\n",MemBytes);


	uint32_t SampleTimeSlow = (SamplingTiming.FastSampleTime <<SamplingTiming.MaxTimeMultiplier)/8000;
	uint32_t BytesPerBlock = 0;
	BytesPerBlock = 22 * ADC_BFR_SIZE  +14;		// assuming 22 bytes per line + 14bytes for the block header

	uint32_t TotalBlocks = 0;

	TotalBlocks = MeasureTime/(SampleTimeSlow * ADC_BFR_SIZE);	// Calculate the total estimated number of blocks

	MemBytes += BytesPerBlock * TotalBlocks;	// Assuming the lowest sample rate this is the number of bytes over the whole measurement duration
	UART_printf("Sampling Bytes %d\n",MemBytes);
	MemBytes += BytesPerBlock * ADC_MAX_MULTIPLIER;				// Add the additional blocks which are required for the log-sampling
	UART_printf("Fast Sampling Bytes %d\n",MemBytes);


	return 0;
}



/**
  * @brief Print the file structure within the flash memory onto the serial port.
  * @param 	lfs_t *lfs		Pointer to the littleFS file system
  * @param  char *path		String of the base directory for printing. Root directory is "/"
  * @retval None
  */
int lfs_ls(lfs_t *lfs, const char *path) {
    lfs_dir_t dir;
    int err = lfs_dir_open(lfs, &dir, path);
    if (err) {
        return err;
    }

    struct lfs_info info;
    while (true) {
        int res = lfs_dir_read(lfs, &dir, &info);
        if (res < 0) {
            return res;
        }

        if (res == 0) {
            break;
        }

        switch (info.type) {
            case LFS_TYPE_REG:
            	UART_printf("reg ");
            	break;
            case LFS_TYPE_DIR: UART_printf("dir "); break;
            default:           UART_printf("?   "); break;
        }

        static const char *prefixes[] = {"", "K", "M", "G"};
        for (int i = sizeof(prefixes)/sizeof(prefixes[0])-1; i >= 0; i--) {
            if ((int32_t)info.size >= (1 << 10*i)-1) {
            	UART_printf("%s%s\t%*u%sB\n", path,info.name, 4-(i != 0), (int32_t)(info.size >> 10*i), prefixes[i]);
                break;
            }
        }
        if (info.type == LFS_TYPE_DIR && strchr(info.name,'.') == 0){
        	char DirName[20] = "";
        	strcat(DirName, info.name);
        	strcat(DirName, "/");
        	lfs_ls(lfs,DirName );
        }
    }

    err = lfs_dir_close(lfs, &dir);
    if (err) {
        return err;
    }

    return 0;
}

