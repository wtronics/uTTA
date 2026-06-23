#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module Name:    utta_SCPI_Driver_Constants.py
Description:    Serial Port SCPI Driver for the uTTA measurement device.
                Constants to make the SCPI driver work
                
Author:         wtronics
Email:          169440509+wtronics@users.noreply.github.com
Date:           11.01.2026
Version:        $VERSION$

--------------------------------------------------------------------------
License:
Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International
(CC BY-NC-SA 4.0)

You are free to share and adapt this material under the following terms:
- Attribution: You must give appropriate credit.
- NonCommercial: You may not use the material for commercial purposes.
- ShareAlike: You must distribute your contributions under the same license.

The full license text can be found at:
https://creativecommons.org/licenses/by-nc-sa/4.0/
--------------------------------------------------------------------------
"""

from enum import Enum

error_codes = {"0.000": "Unknown Error Code",
                            "1.001": "Command Error - Wrong Parameter",
                            "1.002": "Command Error - Too few parameters", 
                            "1.003": "Command Error - Parameter out of range",
                            "1.004": "Command Error - Parameter too long",
                            "1.005": "Command Error - Unknown Command",
                            "1.100": "Command Error - Timeout",
                            "2.000": "Access Error - Measurement running",
                            "2.098": "Access Error - Measurement running",
                            "2.099": "Access Error - Command not allowed in this mode",
                            "3.001": "System Error - No flash memory available",
                            "3.002": "System Error - File exists can't overwrite existing files",
                            "3.003": "System Error - File not found",
                            "3.004": "System Error - Gatedriver Undervoltage",
                            "3.005": "System Error - File Write Error",
                            "3.006": "System Error - ADC Buffer Overrun",
                            "3.007": "System Error - No Device Calibration",
                            "4.172": "File System Error - File System Corrupted",
                            "4.195": "File System Error - No data/attr available",
                            "4.217": "File System Error - Dir is not empty",
                            "4.220": "File System Error - File name too long",
                            "4.228": "File System Error - No space left on device",
                            "4.229": "File System Error - File too large",
                            "4.234": "File System Error - Invalid parameter",
                            "4.235": "File System Error - Entry is a dir",
                            "4.236": "File System Error - Entry is not a dir",
                            "4.239": "File System Error - Entry already exists",
                            "4.244": "File System Error - No more memory available",
                            "4.247": "File System Error - Bad file number",
                            "4.251": "File System Error - Error during device operation",
                            "4.254": "File System Error - No directory entry"}

class MeasureAction(Enum):
    """
    Args:
        Enum (_type_): Start and Stop commands for uTTA measurements
    """    
    STOP = 0
    START = 1   

class SystemModes(Enum):
    """
    Args:
        Enum (_type_): Enum of uTTA System operation modes
    """    
    NORMAL = 0  # Normal measurement mode
    TEST = 1    # Test mode without heating phase
    TEMP = 2    # Not yet implemented measurement mode for TSP calibration

class PGA_GainSetModes(Enum):
    """
    Args:
        Enum (_type_): Selection when to apply the PGA setting
    """    
    ALL = 0         # Apply the PGA setting to heating and cooling phases
    Cooling = 1     # Apply the PGA setting only to cooling phase
    Heating = 2     # Apply the PGA setting only to heating phase

class OffsetChannel(Enum):
    """
    Args:
        Enum (_type_): Selection to which offset channel shall be adressed
    """    
    CH0 = 0         # The heated JUT
    Ch1_2_3 = 1     # The monitored JUT channels

class MeasurementStates(Enum):
    """
    Args:
        Enum (_type_): Current internal state machine state of the uTTA measurement device. 
                        The state numbers equal the internal enum numbers of the uTTA software.
    """    
    Meas_State_Idle = 0		# 0 :  Measurement system is not active
    Meas_State_Init = 1,
    Meas_State_GDPowerCheck = 2,
    Meas_State_InitMeasFile = 3,
    Meas_State_Preheating = 4,
    Meas_State_PrepHeating = 5,
    Meas_State_Heating = 6,
    Meas_State_PrepCooling = 7,
    Meas_State_Cooling =8,
    Meas_State_Deinit = 9,
    Meas_State_CloseLog = 10,
    Test_State_Init = 11,
    Test_State_GDPowerOn = 12,
    Test_State_GPPowerCheck = 13,
    Test_State_Cal = 14,
    Test_State_DeInit = 15,
    Test_State_Exit = 16,
    Temp_State_Init = 17,
    Temp_State_Heat = 18,
    Temp_State_Settle = 19,
    Temp_State_Measure = 20,
    Temp_State_Deinit = 21
