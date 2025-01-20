/*
 * ErrorCodes.h
 *
 *  Created on: 09.08.2022
 *      Author: wtronics
 */

#ifndef INC_ERRORCODES_H_
#define INC_ERRORCODES_H_


#ifdef __cplusplus
extern "C" {
#endif

#include "rtc.h"

typedef struct uTTA_Err_t{
	//RTC_TimeTypeDef ErrTime;
	int8_t ErrCode;
	int8_t SubType;
} Err_t;
#define ERROR_BUFFER_LENGTH 10



// Unknown Command
#define ERRC_COMMAND_ERROR			1

#define ERST_WRONG_PARAM			1
#define ERST_TOO_FEW_PARAM			2
#define ERST_PARAM_OUT_OF_RANGE		3
#define ERST_PARAM_TOO_LONG			4
#define ERST_UNKNOWN_COMMAND		5

#define ERRC_ACCESS_ERROR			2

#define ERST_NOT_ALLOWED_IN_MODE	99
#define ERST_MEAS_RUNNING			0

#define ERRC_SYSTEM_ERROR			3

#define ERST_NO_FLASH_MEMORY				1
#define ERST_FILE_EXISTS			2
#define ERST_FILE_NOT_FOUND			3
#define ERST_GATEDRV_UVLO			4
#define ERST_FILE_WRITE_ERR			5
#define ERST_ADC_BUFFER_OVERRUN		6


#define ERRC_FILE_SYSTEM			4

#define ERST_LFS_ERR_OK          0   //= 0,    // No error
#define ERST_LFS_ERR_IO          251 //= -5,   // Error during device operation
#define ERST_LFS_ERR_CORRUPT     172 //= -84,  // Corrupted
#define ERST_LFS_ERR_NOENT       254 //= -2,   // No directory entry
#define ERST_LFS_ERR_EXIST       239 //= -17,  // Entry already exists
#define ERST_LFS_ERR_NOTDIR      236 //= -20,  // Entry is not a dir
#define ERST_LFS_ERR_ISDIR       235 //= -21,  // Entry is a dir
#define ERST_LFS_ERR_NOTEMPTY    217 //= -39,  // Dir is not empty
#define ERST_LFS_ERR_BADF        247 //= -9,   // Bad file number
#define ERST_LFS_ERR_FBIG        229 //= -27,  // File too large
#define ERST_LFS_ERR_INVAL       234 //= -22,  // Invalid parameter
#define ERST_LFS_ERR_NOSPC       228 //= -28,  // No space left on device
#define ERST_LFS_ERR_NOMEM       244 //= -12,  // No more memory available
#define ERST_LFS_ERR_NOATTR      195 //= -61,  // No data/attr available
#define ERST_LFS_ERR_NAMETOOLONG 220 //= -36,  // File name too long


void InitErrorBuffer(void);
void ErrorResponse(int8_t ErrorCode, int8_t Subtype);		// Prints an error code on the serial port
void ErrorsOutput(void);
void AddError(int8_t ErrorCode, int8_t Subtype);
void EvalLFSError(int32_t LFS_ReturnValue);


#ifdef __cplusplus
}
#endif

#endif /* INC_ERRORCODES_H_ */
