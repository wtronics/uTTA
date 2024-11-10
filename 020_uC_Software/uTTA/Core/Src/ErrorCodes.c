/*
 * ErrorCodes.c
 *
 *  Created on: 18.04.2023
 *      Author: wtronics
 */

#include "ErrorCodes.h"

Err_t ArrErrorBuffer[ERROR_BUFFER_LENGTH];
uint8_t ErrorTotalCount = 0;
/**************************************************************************/
/*!
    @brief  Prints an error code on the serial port
    @param  uint8_t ErrorCode				Error code category
    @param  uint8_t Subtype					Subtype of error
    @returns none
*/
/**************************************************************************/
void ErrorResponse(int8_t ErrorCode, int8_t Subtype){
	UART_printf("Error %d.%03d\n",(uint8_t)ErrorCode,(uint8_t)Subtype);
	AddError(ErrorCode, Subtype);
}


void InitErrorBuffer(void){
	uint8_t Idx = 0;

	for(Idx = 0; Idx < ERROR_BUFFER_LENGTH; Idx++){
		ArrErrorBuffer[Idx].ErrCode = 0;
		ArrErrorBuffer[Idx].SubType = 0;
	}
	ErrorTotalCount = 0;
}


void ErrorsOutput(void){
	uint8_t ErrIdx = 0;
	uint8_t EndIdx = 0;

	if(ErrorTotalCount>=ERROR_BUFFER_LENGTH){
		ErrIdx = ErrorTotalCount%ERROR_BUFFER_LENGTH;
		EndIdx = (ErrorTotalCount%ERROR_BUFFER_LENGTH)-1+ERROR_BUFFER_LENGTH;
	}else{
		ErrIdx = 0;
		EndIdx = ErrorTotalCount;
	}
	UART_printf("Total Errors %d\n",ErrorTotalCount);
	if(ErrorTotalCount){
		for(;ErrIdx<EndIdx;ErrIdx++){
			uint8_t ArrIdx = ErrIdx % ERROR_BUFFER_LENGTH;
			UART_printf("Error %d.%03d ",(uint8_t)ArrErrorBuffer[ArrIdx].ErrCode,(uint8_t)ArrErrorBuffer[ArrIdx].SubType);
			//print_RTC_Time(&ArrErrorBuffer[ArrIdx].ErrTime);
			UART_printf("\n");
		}
	}
}


void AddError(int8_t ErrorCode, int8_t Subtype){

	uint8_t ErrIdx = ErrorTotalCount%ERROR_BUFFER_LENGTH;
	//RTC_read_time(&ArrErrorBuffer[ErrIdx].ErrTime);
	ArrErrorBuffer[ErrIdx].ErrCode=ErrorCode;
	ArrErrorBuffer[ErrIdx].SubType=Subtype;
	ErrorTotalCount++;
}


void EvalLFSError(int32_t LFS_ReturnValue){
	if(LFS_ReturnValue<0){
		AddError(ERRC_FILE_SYSTEM, (int8_t)LFS_ReturnValue);
	}
}
