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
    STOP = 0
    START = 1   

class SystemModes(Enum):
    NORMAL = 0
    TEST = 1
    TEMP = 2

class PGA_GainSetModes(Enum):
    ALL = 0
    Cooling = 1
    Heating = 2

class MeasurementStates(Enum):
    Meas_State_Idle = 0		# 0 :  Measurement system is not active
    Meas_State_Init = 1,
    Meas_State_GDPowerCheck = 2,
    Meas_State_Preheating = 3,
    Meas_State_PrepHeating = 4,
    Meas_State_Heating = 5,
    Meas_State_PrepCooling = 6,
    Meas_State_Cooling =7,
    Meas_State_Deinit = 8,
    Meas_State_CloseLog = 9,
    Test_State_Init = 10,
    Test_State_GDPowerOn = 11,
    Test_State_GPPowerCheck = 12,
    Test_State_Cal = 13,
    Test_State_DeInit = 14,
    Test_State_Exit = 15,
    Temp_State_Init = 16,
    Temp_State_Heat = 17,
    Temp_State_Settle = 18,
    Temp_State_Measure = 19,
    Temp_State_Deinit = 20
