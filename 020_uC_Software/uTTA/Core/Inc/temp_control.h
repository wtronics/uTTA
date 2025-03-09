/*
 * temp_control.h
 *
 *  Created on: Mar 8, 2025
 *      Author: wmdko
 */

#ifndef INC_TEMP_CONTROL_H_
#define INC_TEMP_CONTROL_H_

#ifdef __cplusplus
extern "C" {
#endif

extern float temp_control_steps[10];
extern float temp_control_parameters[];

typedef enum TempControlParameters{
	Num_Tsteps,	// Number of temperature steps to be done
	P,			// Control Loop Proportional parameter
	I,			// Control Loop Integral parameter
	D,			// Control Loop Differential parameter
	T_stable,	// Temperature range in which the temperature is considered stable
	t_Settle,	// Settling Time, time after temperature has reached the stable range
}TempCtrl_Parameter_t;


#ifdef __cplusplus
}
#endif

#endif /* INC_TEMP_CONTROL_H_ */
