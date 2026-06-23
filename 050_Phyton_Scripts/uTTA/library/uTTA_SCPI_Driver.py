#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module Name:    utta_SCPI_Driver.py
Description:    Serial Port SCPI Driver for the uTTA measurement device.
                Includes all necessary functions to control the device.

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

import serial
import serial.tools.list_ports
import threading
import queue
import time
from datetime import datetime
import re
import os
from typing import List, Dict, Any
import library.uTTA_data_import as udi
import library.uTTA_SCPI_Driver_Constants as scpi_consts



def list_serial_ports(pid:str|None=None, vid:str|None=None, name:str|None=None) -> list[dict[str, Any]]:
    """Serial port discovery function to list all available COM-ports (hardware and software ports).
    Optionally filters for USB devices with certain PID, VID or Device Name.

    Args:
        pid (str | None, optional): Filter for USB Device Product ID. Defaults to None.
        vid (str | None, optional): Filter for USB Device Vendor ID. Defaults to None.
        name (str | None, optional): Filter for a certain Device Name. Defaults to None.

    Returns:
        list[dict[str, Any]]: A List of Ports which match the given criteria.
                              The port includes Port Name, Product Name, Vendir ID.
    """

    # get all available serial ports
    ports = serial.tools.list_ports.comports()
    out_ports = []  
    if ports:
        # filter for ports that match the criteria
        for port in ports:
            include = True
            if pid and not f":{pid}" in port.hwid:
                include = False
            if vid and not f"{vid}:" in port.hwid:
                include = False
            if name and not f"{name}" in port.description:
                include = False
            
            port_info = {
                "device": port.device,
                "name": port.description,
                "manufacturer": port.manufacturer if port.manufacturer else "Unknown",
                "hwid": port.hwid
            }
            if include:
                out_ports.append(port_info)

    # terminal output
    # print("+#" * 18 + " Serial Ports (COM & VCP) " + "+#" * 18)
    # if not out_ports:
    #     print("No entries found.")
    #     return

    # for p in out_ports:
    #     print(f"Port: {p['device']}")
    #     print(f"  Name:         {p['name']}")
    #     print(f"  Vendor    :   {p['manufacturer']}")
    #     print(f"  Hardware-ID:  {p['hwid']}")
    #     print("+#" * 49)

    return out_ports

class uTTA_Serial_Communication:
    def __init__(self, port:str, baudrate:int=250000):
        """Serial port communication stack for serial communication with the uTTA measurement device.
        Args:
            port (str): Serial communication port as string in COMxx-format.
            baudrate (int, optional): Baudrate to be used. Defaults to 250000.
        """
        self.ser = serial.Serial(port, baudrate, timeout=1)
        self.running = True
        self.send_termination = '\n'
        self.response_qualifier = None
        self.multiline_response = False
        self.line_count = 0
        self.device_id = None
        self.measurement_running = scpi_consts.MeasureAction.STOP
        # Command response queue
        self.response_queue = queue.Queue()
        
        # Measurement Data queue
        self.meas_data_queue = queue.Queue()

        print(f"Device Name: {self.ser.name}")
        
        # Continious reader thread for serial communication
        self.read_thread = threading.Thread(target=self._reader_loop, daemon=True)
        self.read_thread.start()

        self.error_codes = scpi_consts.error_codes

    def close(self):
        """ Close the serial port.
        """        

        self.running = False
        self.ser.close()
   
    def _flush_received(self):
        """Flushes the receive message queue.
        """

        with self.response_queue.mutex:
            self.response_queue.queue.clear()

    def _reader_loop(self):
        """Serial communication reader loop.
        This loop is started when the COM-port is opened. It will cyclically read from the COM-port and put the received data into one of two queues.
        The first queue is for responses to commands sent to the device. The second queue is for measurement data received from the device.
        The loop will be called by itself in a 5ms period. During this time ~113 characters can be received.
        """
        line = ""
        
        while self.running:
            if self.ser.in_waiting > 0:
                
                if self.multiline_response:
                    last_line = self.ser.readline().decode('utf-8').strip() 
                    line += last_line + "\n"
                    self.line_count += 1
                else:
                    last_line = self.ser.readline().decode('utf-8').strip()
                    line = last_line
                
                # Logic to determine type of latest line
                if str(self.response_qualifier) in str(last_line):
                    # Message is a reaction to some command
                    print(f'Received: \033[95m {line} \033[0m')
                    self.response_queue.put(line)
                    line = ""
                    self.line_count = 0
                elif str(last_line).startswith("Error"):
                    # Message is an error message
                    print(f'\033[91mErr Received: {line} \033[0m')
                    self.response_queue.put(line) 
                    line = ""
                    self.line_count = 0
                    self.measurement_running = scpi_consts.MeasureAction.STOP
                elif str(last_line).startswith("#M;"):
                    # measurement data
                    print(f'Meas  Received: \033[94m {line} \033[0m')
                    self.meas_data_queue.put(line)
                    self.line_count = 0
                elif str(last_line).startswith("Measurement completed!"):
                    self.measurement_running = scpi_consts.MeasureAction.STOP

            else:
                time.sleep(0.005)  # reduce CPU-load. @ 250kbaud 5ms equals rougly 113 new characters. (250.000 Sym / 11 Sym/Character) * 5ms

    def _send_command_async(self, cmd:str, resp_qualifier:str|None=None, timeout:float=2,  multiline_response:bool=False):
        """Sends a command and does not wait for a response.

        Args:
            cmd (str): The SCPI command to be sent.
            resp_qualifier (str | None, optional): Defines the qualifier which is expected at the beginning of the response. Set to None if no response is expected. Defaults to None.
            timeout (float, optional): Set the timeout in seconds. Defaults to 2.
            multiline_response (bool, optional): Set to True in case the expected response consists of more than a single line. Defaults to False.
        """ 
        # Make sure the queue is empty before sending a new command
        while not self.response_queue.empty():
            self.response_queue.get()

        # save the expected qualifier for the response
        self.response_qualifier = resp_qualifier
          
        full_cmd = f"{cmd}{self.send_termination}".encode('utf-8')
        print(f'Sending: \033[96m {full_cmd}, Multiline: {multiline_response}\033[0m')
        self.multiline_response = multiline_response
        self.ser.write(full_cmd)
    
    def _check_async_command_complete(self) -> tuple[bool, str]:
        """Check if a non blocking way if the expected response has been received.

        Returns:
            tuple[bool, str]: Set to True in case a valid message has been received, Contains the raw response. 
            In case an error was removed, the Message contains the error ID.
        """
        try:
            # wait for the specific answer from the reader thread
            response = str(self.response_queue.get(timeout=0.001))
            return self.__validate_response(response)
        except queue.Empty:
            return False, ""

    def check_measurement_complete(self) -> bool:
        """Check if the current measurement has been completed.

        Returns:
            bool: True if the measurement is completed.
        """     
        if self.measurement_running == scpi_consts.MeasureAction.START:
            return False
        return True
    
    def get_measurement_data(self) -> tuple[bool, str]:
        """Read the latest data from the measurement data queue. 
        Will return false and an empty string when no data are availible.

        Returns:
            tuple[bool, str]: True when measurement data are available, Received string.
        """        
        if not self.meas_data_queue.empty():
            return True, self.meas_data_queue.get()
        return False, ""

    def _send_command(self, cmd:str, resp_qualifier:str|None=None, timeout:float=2,  multiline_response:bool=False) -> tuple[bool, str]:
        """Sends an SCPI-command and waits for the response. The response must start with the matching response qualifier.

        Args:
            cmd (str): The SCPI command to be sent
            resp_qualifier (str|None, optional): Defines the qualifier which is expected at the beginning of the response. Set to None if no response is expected. Defaults to None.
            timeout (float, optional):  Set the timeout in seconds. Defaults to 2.
            multiline_response (bool, optional): Set to True in case the expected response consists of more than a single line. Defaults to False.

        Returns:
            tuple[bool, str]: Set to True in case a valid message has been received, Contains the raw response. 
            In case an error was removed, the Message contains the error ID.
        """        

        # Make sure the queue is empty before sending a new command
        while not self.response_queue.empty():
            self.response_queue.get()

        # save the expexted qualifier for the response
        self.response_qualifier = resp_qualifier
          
        full_cmd = f"{cmd}{self.send_termination}".encode('utf-8')
        print(f'Sending: \033[96m {full_cmd}, Multiline: {multiline_response}\033[0m')
        self.multiline_response = multiline_response
        match cmd:
            case  s if s.startswith("MEAS:START"):
                self.measurement_running = scpi_consts.MeasureAction.START
            case  s if s.startswith("MEAS:STOP"):
                self.measurement_running = scpi_consts.MeasureAction.STOP

        self.ser.write(full_cmd)
        
        if self.response_qualifier:
            try:
                # wait for the specific answer from the reader thread
                response = self.response_queue.get(timeout=timeout)
                return self.__validate_response(response)
            except queue.Empty:
                return False,f"1.100 {self.error_codes["1.100"]}"
        else:
            return True, "No Query"

    def __validate_response(self, response:str) -> tuple[bool, str]:
        """Validates the device response against the expected response qualifier.

        Args:
            response (str): The received message from the device.

        Returns:
            tuple[bool, str]: True in case the message matches the response qualifier, String containts either the message of an Error Message.
        """        
        err_code = "0.000"
        if str(self.response_qualifier) in response:
            self.response_qualifier = None  # found the expected response therefore, the qualifier can be removed
            return True, response
        elif response.startswith("Error"):
            err_code = response.replace("Error ", "")
            if err_code in self.error_codes:
                err_text = f'{err_code} {self.error_codes[err_code]}'
            else:
                err_text = f'{err_code} Error - Unknown Error'

            return False, err_text
        return False, f'{err_code} Error -  Unknown Response Format'

    def identify_instrument(self) -> tuple[bool, str]:
        """Send an SCPI identification request and checks if the response matches a uTTA device response.

        Returns:
            tuple[bool, str]: True when successful, String contains the full response from the device.
        """        

        success, msg = self._send_command("*IDN?", resp_qualifier=", uTTA, SN")
        if success:
            dev_sn = msg.split(", uTTA, SN")[1]
            dev_sn = dev_sn.split(",")[0]
            self.device_id = f"SN{dev_sn.strip()}"
            print(f"Device Serial Number: {self.device_id}")
        return success, msg

    def reset_instrument(self) -> tuple[bool, dict]:
        """Performs a device reset and parses the resulting debug output at the restart.

        Returns:
            tuple[bool, dict]: True if sucessful. The dictionary returns full device information. 
                               In case of an error only the corresponding error message is responded.
        """        
        success, msg = self._send_command("*RST", resp_qualifier="RTC Time: ", timeout=10, multiline_response=True)
        info = {}
        if success:
            lines = msg.splitlines()
            for line in lines:
                match line:
                    case  s if s.startswith("Manufacturer"):
                        info["Memory_Manufacturer"] = int(line.replace("Manufacturer       = ", "").strip(), 16)
                    case  s if s.startswith("Device"):                
                        info["Memory_Device_Type"] = int(line.replace("Device             = ", "").strip(), 16)
                    case  s if s.startswith("Block size"):          
                        line = line.replace("Block size         = ", "").strip()
                        items = line.split(" ")
                        info["Block_Size"] = int(items[0], 16)
                    case  s if s.startswith("Block count"):          
                        line = line.replace("Block count        = ", "").strip()
                        items = line.split(" ")
                        info["Block_Count"] = int(items[0], 16)
                    case  s if s.startswith("Total size (in kB)"):          
                        line = line.replace("Total size (in kB) = ", "").strip()
                        items = line.split(" ")
                        info["Total_Size_kB"] = int(items[0], 16)
                    case  s if s.startswith("CALIBRATION_FILE:"):          
                        line = line.replace("CALIBRATION_FILE: ", "").strip()
                        if line == "Available":
                            info["Calibration_File"] = True
                        else:
                            info["Calibration_File"] = False   
        else:
            info["Error"] = msg
        return success, info

    def get_system_clock(self) -> tuple[bool, datetime | None]:
        """Reads the uTTA device system clock current time and returns it in datetime format.

        Returns:
            tuple[bool, datetime | None]: True and date + time if sucessful, otherwise False and None.
        """        
        self._flush_received()
        success, msg =  self._send_command("SYST:CLOCK?", resp_qualifier="#TIME")
        if success:
            msg = msg.replace("#TIME ", "")
            date_time = datetime.strptime(msg, '%d.%m.%Y %H:%M:%S')
            return success, date_time
        return success, None
 
    def sync_system_time(self):
        """Checks the current date and time of the uTTA system real time clock against the PC clock.
        In case of a difference of more than 10 seconds the device clock is updated to the current time of the PC clock.
        """        
        success, utta_time = self.get_system_clock()
        system_time = datetime.now()
        if utta_time:
            d_time = abs(utta_time-system_time)

            print(f"System Time {system_time}, uTTA-Time {utta_time}, Difference {d_time.seconds}")

            if d_time.seconds >= 10:        # difference is larger than 10 seconds, therefore a synchronisation is done
                self.set_system_date(datetime.now())
                self.set_system_time(datetime.now())
    
    def set_system_time(self, sys_time:datetime) -> bool:
        """Set the uTTA devices system time (not date!) to the given time.

        Args:
            sys_time (datetime): Time to be set to the device.

        Returns:
            bool: Returns true when executed sucessfully.
        """        
        success = False
        if sys_time:
            timestr = datetime.strftime(sys_time, "%H,%M,%S")
            success, msg =  self._send_command(f"SYST:CLOCK TIME,{timestr}")
        return success

    def set_system_date(self, sys_date:datetime) -> bool:
        """Set the uTTA devices system data (not time!) to the given date.

        Args:
            sys_date (datetime): Date to be set to the device.

        Returns:
            bool: Returns true when executed sucessfully.
        """    
        success = False
        if sys_date:
            datestr = datetime.strftime(sys_date, "%d,%m,%Y")
            success, msg =  self._send_command(f"SYST:CLOCK DATE,{datestr}")
        return success

    def memory_speedtest(self) -> int:
        """Performs a memory speed test to check if the attached SPI flash can keep up with the demands during
        the high sample rate period of the measurement.
        This function is locked during any measurement and can only be performed while the measurement is stopped. 

        Returns:
            int: Returns the needed time in Miliseconds, -1 in case of an error.
        """        

        success, msg =  self._send_command(f"MEM:WRITE", resp_qualifier="Write took ", timeout=30)
        if success:
            msg = msg.replace("Write took ","").replace(" ms","")
            return int(msg)
        return -1

    def delete_file(self, file_name:str) -> bool:
        """Deletes a file from the SPI flash file system. This function can't delete folder, files only!
        This function is locked during any measurement and can only be performed while the measurement is stopped. 

        Args:
            file_name (str): File name including folder name and file extension.

        Returns:
            bool: True when executed sucessful.
        """        
        success = False

        if file_name:
            success, msg =  self._send_command(f"MEM:DEL  {file_name}", resp_qualifier="Deleted: ")
            if success:
                msg = msg.replace("Deleted: ", "")
        return success
    
    def write_calibration_file(self, file_name:str) -> bool:
        """Writes the uTTA device calibration data from a given calibration file to the device.
        To perform this operation the existing device calibration must be deleted before writing a new calibration file.
        Furthermore, the device serial number in the calibration file must match the serial number of the connected device.
        Otherwise, the calibration file will not be written to the device.
        This function is locked during any measurement and can only be performed while the measurement is stopped. 

        Args:
            file_name (str): Path to the calibration file to be written. The file extension must end with *.ucf

        Returns:
            bool: Returns True when executed with success, otherwise False.
        """        
        success = False

        if file_name.endswith(".ucf"):
            dev_cal_data, dev_meta_data ,_ ,_ = udi.read_calfile2dict(file_name) 
            
            dev_serial = dev_meta_data["DEVICE_INFO"]["SN"].replace('"','')
            print(f"Calibration file for {dev_serial}")
            if dev_serial == self.device_id:
                success_all = True
                scaling_factor = 1.0
                for key, cal_set in dev_cal_data.items():

                    print(f"SYST:CAL {key},{cal_set["Offset"]*scaling_factor},{cal_set["LinGain"]*scaling_factor},{cal_set["QuadGain"]*scaling_factor}")
                    success, msg =  self._send_command(f"SYST:CAL {key},{cal_set["Offset"]*scaling_factor},{cal_set["LinGain"]*scaling_factor},{cal_set["QuadGain"]*scaling_factor}", 
                                                        resp_qualifier="#CAL ")
                    success_all = success_all and success
                if success_all:
                    success, msg = self._send_command("SYST:SAVE", resp_qualifier="Calibration written")
                    success_all = success_all and success
                return success_all
            # TODO: Test that this all works
            else:
                print("Device ID doesn't match calibration file")
        return success

    def read_directory(self,directory:str=r'/') -> tuple[bool, str | list]:
        """Recursively reads the contents of a directory. Files and Folders are reported in a list of strings.
        This function is locked during any measurement and can only be performed while the measurement is stopped. 

        Args:
            directory (str, optional): The root folder for reading the directory and everything below it. Defaults to r'/'.

        Returns:
            tuple[bool, str | list]: True if executed without error, otherwise False. 
            When sucessful a list of strings is returned. Each line contains a folder or file. 
            On Error the error message is reported as a single string
        """        
        outfiles = []

        success, msg =  self._send_command(f"MEM:DIR {directory}", resp_qualifier="#END", multiline_response=True)
        if success:
            lines = msg.splitlines()
            for line in lines:
                if line.startswith("reg "):
                    items = line.replace("reg ", "").split('\t')
                    fil = {"Name":items[0], "Size": items[1]}
                    outfiles.append(fil)
        else:
            outfiles = msg

        return success, outfiles
    
    def download_file(self,file_name:str=r'/', timeout:int=300) -> tuple[bool, str]:
        """downloads a measurement file from the uTTA device. 
        This function blocks during download.

        Args:
            file_name (str, optional): Name of the file to be downloaded. The file name must include the folder name and file extension. Defaults to r'/'.
            timeout (int, optional): Timeout for the download operation in seconds. Defaults to 300.

        Returns:
            tuple[bool, str]: True if successful, otherwise false. String contains the downloaded file (error message when failed).
        """
        success, msg =  self._send_command(f"MEM:READ {file_name}", resp_qualifier="Read took ", timeout=timeout, multiline_response=True)
        if success:
            msg = self.process_downloaded_file(msg)
        return success, msg
    
    def download_file_v2(self,file_name:str=r'/', timeout:int=300):
        """downloads a measurement file from the uTTA device. 
        This is a non blocking function. Download progress must be checked in a spearate call. 
        
        Args:
            file_name (str, optional): Name of the file to be downloaded. The file name must include the folder name and file extension. Defaults to r'/'.
            timeout (int, optional): Timeout for the download operation in seconds. Defaults to 300.
        """
        self._send_command_async(f"MEM:READ {file_name}", resp_qualifier="Read took ", timeout=timeout, multiline_response=True)
        # Example implementation of a possible read out of the progress
        # while True:
        #     success, msg = self._check_async_command_complete()
        #     if success:
        #         return success, self.process_downloaded_file(msg)     
        #     else:
        #         print(f"Number of lines read: {self.line_count}")
        #         time.sleep(0.2)
    
    def process_downloaded_file(self, fil_data:str) -> str:
        """ Processing of the received message after download.
        This is needed to remove additional lines which are sent during the download.

        Args:
            fil_data (str): The received data

        Returns:
            str: The processed file data without header and footer
        """        
        lines = fil_data.splitlines()
        del lines[0]
        del lines[-1]
        msg = '\n'.join(lines)
        return msg

    def upload_file(self, file_path:str) -> tuple[bool, dict]:
        """Upload of a file to the uTTA device.
        This function is locked during any measurement and can only be performed while the measurement is stopped. 

        Args:
            file_path (str): Path to the file to be uploaded

        Returns:
            tuple[bool, dict]: Returns True when executed with success, otherwise False. Dict of status messages.
        """        
        status = {}
        success = False
        if file_path:
            file_name = os.path.basename(file_path)

            with open(file_path, 'r') as send_file:
                file_content = send_file.readlines()
            
            success, status = self.__file_upload(file_name, file_content)
        
        return success, status

    def __file_upload(self,file_name:str, file_contents:list[str], interline_delay:float=0.02) -> tuple[bool, dict]:
        """Private upload function to upload the file contents

        Args:
            file_name (str): File name and file extension. Max file name length is 16 characters
            file_contents (list[str]): The content of the file to be uploaded
            interline_delay (float, optional): Delay between lines to give the uTTA device a little time to digest the last line. Defaults to 0.02.

        Returns:
            tuple[bool, dict]: Returns True when executed with success, otherwise False, Dictionary of status messages
        """
        tx_max_chunk_size = 64
        status = {}
        l_delay = min(1.0, max(interline_delay, 0.01))

        f_name = re.sub("[^a-zA-Z0-9._]", '_', file_name)
        f_name_parts = f_name.split(".")
        name = f_name_parts[0]
        max_chars = 16 - (1 + len(f_name_parts[-1]))
        f_name_parts[0] = (name[:max_chars]) if len(name) > max_chars else name   # limit string to length
        f_name = ".".join(f_name_parts)

        success, msg =  self._send_command(f"MEM:UPL {f_name}", resp_qualifier="Entering File upload Mode for File:", timeout=5)
        if success:
            status["File_Name"] = msg.replace("Entering File upload Mode for File:", "").strip()
            for line in file_contents:
                if len(line) > tx_max_chunk_size:
                    print(f"Line >{line}< is too long. This line will be shortened!")
                    line = (line[:tx_max_chunk_size])  
                
                if len(line.strip()) <1: 
                    print("\033[95m Padding empty line\033[0m")
                    line = "#"
                success, msg = self._send_command(f"{line.strip()}", resp_qualifier="Writing: ")
                time.sleep(l_delay) # limit the speed to give the MCU time to keep up

                if not success:
                    status["Error"] = msg
                    break

            success, msg =  self._send_command(f"<EOF>", resp_qualifier="Received end of file flag, closing file!", timeout=5)
            if not success:
                status["Error"] = msg
        else:
            status["Error"] = msg

        return success, status

    def set_cooling_time(self, t_cool:int) -> tuple[bool, dict]:
        """Set the cooling time for the next measurement.
        The cooling time is the interval between the heating time and the end of the measurement.
        This parameter is locked during any measurement and can only be written while the measurement is stopped. 

        Args:
            t_cool (int): Cooling time in seconds. Accepted Range: 60...21600 seconds

        Returns:
            tuple[bool, dict]: Returns True when executed with success, otherwise False. Dictionary of status messages
        """        
        success = False
        status = {}
        if t_cool >= 0:
            success, msg =  self._send_command(f"MEAS:TIM:COOL {t_cool*1000}", resp_qualifier="MEAS:TIM ")
            if success:
                status = self.__parse_timing_response(msg)
            else:
                status["Error"] = msg
        return success, status
    
    def set_heating_time(self, t_heat:int) -> tuple[bool, dict]:
        """Set the heating time. The heating time is the period when the JUT is heated by the heating current.
        This parameter is locked during any measurement and can only be written while the measurement is stopped. 

        Args:
            t_heat (int): Heating time in seconds. Range: 60s to 10800s. 
                          When set to 0 the device will to a TSP calibration measurement, thus the only relevant time is the pre-heating time.

        Returns:
            tuple[bool, dict]: Returns True when executed with success, otherwise False. Dictionary of status messages
        """        
        success = False
        status = {}
        if t_heat >= 0:
            success, msg =  self._send_command(f"MEAS:TIM:HEAT {t_heat*1000}", resp_qualifier="MEAS:TIM ")
            if success:
                status = self.__parse_timing_response(msg)
            else:
                status["Error"] = msg
        return success, status
    
    def set_preheating_time(self, t_preheat:int) -> tuple[bool, dict]:
        """Set the pre-heating time. The heating time is the period when the JUT is heated by the heating current.
        This parameter is locked during any measurement and can only be written while the measurement is stopped. 
        Args:
            t_heat (int): Pre-heating time in seconds. Range: 30s to 21600s. 

        Returns:
            tuple[bool, dict]: Returns True when executed with success, otherwise False. Dictionary of status messages
        """   
        success = False
        status = {}
        if t_preheat >= 0:
            success, msg =  self._send_command(f"MEAS:TIM:PRE {t_preheat*1000}", resp_qualifier="MEAS:TIM ")
            if success:
                status = self.__parse_timing_response(msg)
            else:
                status["Error"] = msg
        return success, status

    def get_time_settings(self) -> tuple[bool, dict]:
        """Querys the current timing setting from the device. 

        Returns:
            tuple[bool, dict]: Returns True when executed with success, otherwise False. 
                               Dictionary of status messages containing T_Preheat, T_Heat and T_Cool. 
                               In case of a error only the 'Error' element will be returned.
        """        
        status = {}
        success, msg =  self._send_command(f"MEAS:TIME?", resp_qualifier="MEAS:TIM ")
        if success:
            status = self.__parse_timing_response(msg)
        else:
            status["Error"] = msg
        return success, status
    
    def __parse_timing_response(self, time_resp:str) -> dict:
        """Parses a time response string returned from the device into a usable format.

        Args:
            time_resp (str): The string received from the device.

        Returns:
            dict: Dictionary of status messages containing T_Preheat, T_Heat and T_Cool. 
                  In case of a error only the 'Error' element will be returned.
        """        
        measure_times = {}
        if time_resp:      
            times = time_resp.replace("MEAS:TIM ", "").split(";")
            if len(times)==3:
                measure_times['T_Preheat'] = int(times[0])/1000
                measure_times['T_Heat'] = int(times[1])/1000
                measure_times['T_Cool'] = int(times[2])/1000
            else:
                measure_times['Error'] = "Too few parameters returned"
        return measure_times

    def set_dut_name(self, dut_name:str) -> tuple[bool, dict]:
        """Set the DUT name. Basically this sets the file name for the next measurent.
        The file name shall not include a file extension. This is done by the uTTA device itself.
        This parameter is locked during a normal measurement and can only be written while the
        measurement is stopped. In Test-Mode the parameter can be changed on the fly.

        Args:
            dut_name (str): The DUT name for the next measurement. The filename shall not include any special characters.
                            Only A-Z, a-z, 0-9 and _ are allowed characters. Max. length of the file name is 50 characters

        Returns:
            tuple[bool, dict]: True when executed with success, otherwise False. 
                               Dictionary of status messages containing 'DUT_Name'. 
                               In case of a error only the 'Error' element will be returned.
        """        
        success = False
        status = {}
        max_chars = 50
        if dut_name:
            name = (dut_name[:max_chars]) if len(dut_name) > max_chars else dut_name   # limit string to length
            name = re.sub("[^a-zA-Z0-9]", '_', name)
            
            success, msg =  self._send_command(f"MEAS:DUT {name}", resp_qualifier="OK ")
            if success:
                status["DUT_Name"] = msg.replace("OK ", "").strip()
        else:
            status["Error"] = "No DUT name given"

        return success, status

    def set_ch_description(self, meas_ch_no:int, ch_name:str, ch_cal:dict) -> tuple[bool, dict]:
        """Sets the description and channel parameters of a single measurement channel.
        This parameter is locked during a normal measurement and can only be written while 
        the measurement is stopped. In Test-Mode the parameter can be changed on the fly.

        Args:
            meas_ch_no (int): The number of the channel to be set. The heated channel is channel no 0, monitored channels are 1, 2 (and 3).
            ch_name (str): Name of the channel as string. Max string length is 30 characters.
            ch_cal (dict): Channel calibration dictionary. Contains the following items: Offset, LinGain, QuadGain, CalStatus.

        Returns:
            tuple[bool, dict]: True when executed with success, otherwise False. 
                               Dictionary of status messages containing: CH_No, CH_Name, Offset, LinGain, QuadGain.
                               In case of a error only the 'Error' element will be returned.
        """        
        success = False
        msg = "Parameter Error"
        key_names = ["Offset", "LinGain", "QuadGain", "CalStatus"]
        ret_params:dict = {}

        for k in key_names:
            if not k in ch_cal:
                ret_params["Error"]  = "Missing parameter in calibration " + k
                return success, ret_params
            
        if 0 <= meas_ch_no <= 3:
            max_chars = 30
            name = (ch_name[:max_chars]) if len(ch_name) > max_chars else ch_name   # limit string to length
            name = re.sub("[^a-zA-Z0-9]", '_', name)
            scale = 1000000
            #print(f"MEAS:CHDESC {meas_ch_no},{name},{ch_cal["Offset"]*scale},{ch_cal["LinGain"]*scale},{ch_cal["QuadGain"]*scale},{ch_cal["CalStatus"]}")
            success, msg =  self._send_command(f"MEAS:CHDESC {meas_ch_no+1},{name},{ch_cal["Offset"]*scale},{ch_cal["LinGain"]*scale},{ch_cal["QuadGain"]*scale},{ch_cal["CalStatus"]}", resp_qualifier="#CH ")
            
            if success:
                msg = msg.replace("#CH ", "")
                params = msg.split(";")

                ret_params["CH_No"] = int(params[0])
                ret_params["CH_Name"] = str(params[1])
                ret_params["Offset"] = float(params[2])
                ret_params["LinGain"] = float(params[3])
                ret_params["QuadGain"] = float(params[4])
            else:
                ret_params["Error"] = msg
        else:
            ret_params["Error"]  = f"1.003 {self.error_codes["1.003"]}"
        return success, ret_params

    def set_measure(self, action:scpi_consts.MeasureAction) -> tuple[bool, str]:
        """Starts or Stops the measurement. Once a measurement is started the device needs to be stopped before starting a new measurement.

        Args:
            action (scpi_consts.MeasureAction): Use START to start a measurement and STOP to stop it.
        Returns:
            tuple[bool, str]: True when executed with success, otherwise False.  
                              In case of an error an 'Error'-string will be returned.
        """        
        if action == scpi_consts.MeasureAction.START:
            return  self._send_command(f"MEAS:START", resp_qualifier="OK")
        elif action == scpi_consts.MeasureAction.STOP:
            return  self._send_command(f"MEAS:STOP", resp_qualifier="Measurement completed!", timeout=15)

    def set_mode(self, mode:scpi_consts.SystemModes) -> tuple[bool, str]:
        """ Set the measurement operating mode of the uTTA device.
            This parameter is locked during any measurement and can only be written while the measurement is stopped.

        Args:
            mode (scpi_consts.SystemModes): Sets the operating mode as enum.

        Returns:
            tuple[bool, str]: True when executed with success, otherwise False.  
                              In case of an error an 'Error'-string will be returned.
        """        
       
        return  self._send_command(f"SYST:MODE {mode.name}", resp_qualifier="OK")
      
    def get_system_calibration(self) -> tuple[bool, dict]:
        """Reads the current system calibration from the uTTA device. 

        Returns:
            tuple[bool, dict]: True when executed with success, otherwise False. 
                               Dictionary of status messages containing the full uTTA device calibration information. 
                               In case of a error only the 'Error' element will be returned.
        """        
        out_cal = {}

        success, msg =  self._send_command(f"SYST:CAL?", resp_qualifier="#EOF", multiline_response=True)
        if success:
            lines = msg.splitlines()
            for line in lines:
                line_cols = line.split(",")
                scale = 1.0
                if len(line_cols) == 4:
                    match line:
                        case s if s.startswith('DAC_ISEN'):
                            scale = 1.0/1000000.0
                        case s if s.startswith('DAC_OFF'):
                            scale = 1.0/1000000.0

                    out_cal[str(line_cols[0])]={"Offset": float(line_cols[1])*scale, "LinGain": float(line_cols[2])*scale, "QuadGain": float(line_cols[3])*scale}
        else:
            out_cal["Error"] = msg

        return success, out_cal
    
    def get_system_error_status(self) -> tuple[bool, list]:
        """Reads the current error status from the uTTA measurement device.

        Returns:
            tuple[bool, list]: True when executed with success, otherwise False.  
                               In case of an error only one element with an 'Error'-string will be returned.
        """        
        outfiles = []

        success, msg =  self._send_command(f"*ESR?", resp_qualifier="#ERR", multiline_response=True)
        if success:
            lines = msg.splitlines()
            for line in lines:
                pass # TODO: Parsing of returned values
        else:
            outfiles.append(msg)

        return success, outfiles
    
    def get_system_status(self) -> tuple[bool, dict]:
        """Reads the uTTA System Status.

        Returns:
            tuple[bool, dict]: True when executed with success, otherwise False.  
                               In case of an error an 'Error'-string will be returned.
        """        
        ret_val = {}
        success, msg =  self._send_command(f"*STB?", resp_qualifier="SYST:STAT ")
        if success:
            print(msg)
            msg = msg.replace("SYST:STAT ", "").strip()
            ret_val = {"Errors": int(msg[:2], 16),
                       "Status": int(msg[2:], 16)}
        else:
            ret_val["Error"] = msg
        return success, ret_val
    
    def set_offset_voltage(self, channel:scpi_consts.OffsetChannel, voltage:float) -> tuple[bool, str]:       
        """Set the channels offset voltage to get the measured voltage of the JUT into the ADC range.
        The settable range ist roughly between -2.5V and 2.5V. Nevertheless, the gain of the last 
        amplifier stage will limit the useful range to less.
        This parameter is locked during a normal measurement and can only be written while the 
        measurement is stopped. In Test-Mode the parameter can be changed on the fly.

        Args:
            channel (scpi_consts.OffsetChannel): Number of the channel to be set. 
            voltage (float): Offset voltage to be applied. Typically the set voltage is NEGATIVE and in VOLTS.

        Returns:
            tuple[bool, str]: True when executed with success, otherwise False.  
                              In case of an error an 'Error'-string will be returned.
        """        
        ret_val = 0

        success, msg =  self._send_command(f"MEAS:SET VOFF,{channel.value},{voltage*1000}", resp_qualifier="OK ")
        if success:
            ret_val = int(msg.replace("OK ", "").strip())
            if ret_val == -2:
                msg  = f"1.003 {self.error_codes["1.003"]}"
                success = False
            elif ret_val == 2:
                msg  = f"3.007 {self.error_codes["3.007"]}"     # No device calibration
                success = False
            elif ret_val == 1:
                msg  = "OK"    
            else:         
                msg  = f"1.003 {self.error_codes["1.003"]}"
                success = False
        return success, msg
    
    def set_sense_current(self, channel:int, i_sense:float) -> tuple[bool, str]:
        """Set the channels sense current for sensing the JUT temperatures.
        The settable range ist roughly between 10µA and 11mA. Typically 10mA is a good value to start with.
        The channel input parameter is a placeholder in case this value will be settable on a channel basis in the future.
        This parameter is locked during a normal measurement and can only be written while the measurement is stopped. 
        In Test-Mode the parameter can be changed on the fly.
        Args:
            channel (scpi_consts.OffsetChannel): This value is not used right now. Internally it will be overwritten to 0.
            i_sense (float): Sense current to be applied. This value is set in AMPS.

        Returns:
            tuple[bool, str]: True when executed with success, otherwise False.  
                              In case of an error an 'Error'-string will be returned.
        """  
        ret_val = 0
        channel = 0
        success, msg =  self._send_command(f"MEAS:SET ISEN,{channel},{i_sense*1000000}", resp_qualifier="OK ")
        if success:
            ret_val = int(msg.replace("OK ", "").strip())
            if ret_val == -2:
                msg  = f"1.003 {self.error_codes["1.003"]}"
                success = False
            elif ret_val == 2:
                msg  = f"3.007 {self.error_codes["3.007"]}"     # No device calibration
                success = False
            elif ret_val == 1:
                msg  = "OK"   
            else:          
                msg  = f"1.003 {self.error_codes["1.003"]}"
        return success, msg

    def set_pga_gain(self, gain:int, mode:scpi_consts.PGA_GainSetModes) -> tuple[bool, dict]:
        """Sets the PGA gain for channel 0 (the heated channel). This parameter is locked during a normal measurement
        and can only be written while the measurement is stopped. In Test-Mode the parameter can be changed on the fly.

        Args:
            gain (int): Set value of the gain stage. At the moment values from 0 to 3 are supported.
            mode (scpi_consts.PGA_GainSetModes): Defines in which measurement phase the new setting is applied (Heating, Cooling or All).
        Returns:
            tuple[bool, dict]: True when executed with success, otherwise False. 
                               Dictionary of status messages containing: Current PGA Setting, Cooling PGA Setting and Heating PGA Setting.
                               In case of a error only the 'Error' element will be returned.
        """        
        measure_gains = {}
        if mode == scpi_consts.PGA_GainSetModes.ALL:
            success, msg =  self._send_command(f"SYST:GAIN {gain}", resp_qualifier="#PGA ")
        else:
            success, msg =  self._send_command(f"SYST:GAIN {mode.name.upper()},{gain}", resp_qualifier="#PGA ")
        if success:
            measure_gains = self.__parse_pga_gains(msg)
        else:
            measure_gains['Error'] = msg

        return success, measure_gains
    
    def get_pga_gain(self) -> tuple[bool, dict]:
        """Reads the PGA settings for the heated channels PGA from the device. 
        There is no dedicated getter function for each setting. 
        This function will return the settings for all phases including the currently applied setting.

        Returns:
            tuple[bool, dict]: True when executed with success, otherwise False. 
                               Dictionary of status messages containing: Current PGA Setting, Cooling PGA Setting and Heating PGA Setting.
                               In case of a error only the 'Error' element will be returned.
        """        
        measure_gains = {}
        success, msg =  self._send_command(f"SYST:GAIN?", resp_qualifier="#PGA ")
        if success:
            measure_gains = self.__parse_pga_gains(msg)
        else:
            measure_gains['Error'] = msg

        return success, measure_gains
    
    def __parse_pga_gains(self, msg:str) -> dict:
        """Private function to parse the received string into a more useable format.

        Args:
            msg (str): The received message from the uTTA device after writing or reading PGA settings.

        Returns:
            dict: Dictionary of status messages containing: Current PGA Setting, Cooling PGA Setting and Heating PGA Setting. 
            In case of a error only the 'Error' element will be returned.
        """        
        measure_gains = {}
        gains = msg.replace("#PGA ", "").strip().split(";")
        if len(gains)==3:
            measure_gains = {"Set": int(gains[0]),
                            "Cooling": int(gains[1]),
                            "Heating": int(gains[2]) }
        else:
            measure_gains['Error'] = "Too few parameters returned"
        return measure_gains

    def control_ext_power_supply(self, enable:bool) -> tuple[bool, dict]:
        """Controls the output for the external power supply (the optocoupler).
        This output can be used to control an external power supply.
        e.g. it can be used to disable the power supply after the heating
        phase to reduce leakage currents through the MOSFET stage.
        This parameter is locked during a normal measurement and can only be written while 
        the measurement is stopped. In Test-Mode the parameter can be changed on the fly.

        Args:
            enable (bool): Control value for the power supply. True = ON

        Returns:
            tuple[bool, dict]: True when executed with success, otherwise False. 
                               Dictionary of status messages containing: PSU with the current state of the output.
                               In case of a error only the 'Error' element will be returned.
        """        
        status = {}
        success, msg =  self._send_command(f"SYST:PSU {enable}", resp_qualifier="#PSU ")
        if success:
            status['PSU'] = bool(int(msg.replace("#PSU ", "")))
        else:
            status['Error'] = msg

        return success, status

    def get_ext_power_supply(self) -> tuple[bool, dict]:
        """Read the current control status of the external power supply output.

        Returns:
            tuple[bool, dict]: True when executed with success, otherwise False. 
                               Dictionary of status messages containing: PSU with the current state of the output.
                               In case of a error only the 'Error' element will be returned.
        """        
        status = {}
        success, msg =  self._send_command(f"SYST:PSU?", resp_qualifier="#PSU ")
        if success:
            status['PSU'] = bool(int(msg.replace("#PSU ", "")))
        else:
            status['Error'] = msg

        return success, status

    def control_gate_driver_power(self, enable:bool) -> tuple[bool, dict]:
        """Controls the power supply for the powerstage.
        e.g. it can be used to disable the power supply for the power stage  after the 
        heating phase to reduce quiesent current and improve battery lifetime.
        This parameter is locked during a normal measurement and can only be written while 
        the measurement is stopped. In Test-Mode the parameter can be changed on the fly.

        Args:
            enable (bool): True enables the power supply for the gate driver.

        Returns:
            tuple[bool, dict]: True when executed with success, otherwise False. 
                               Dictionary of status messages containing: 'Gate_Drive_Power' with 
                               the current state of the power supply for the power stage.
                               In case of a error only the 'Error' element will be returned.
        """        
        status = {}
        success, msg =  self._send_command(f"SYST:GDPOW {enable}", resp_qualifier="#GD ")
        if success:
            status['Gate_Drive_Power'] = bool(int(msg.replace("#GD ", "")))
        else:
            status['Error'] = msg

        return success, status
    
    def get_gate_driver_power(self) -> tuple[bool, dict]:
        """Read the current state of the power supply for the power stage from the uTTA device.

        Returns:
            tuple[bool, dict]: True when executed with success, otherwise False. 
                               Dictionary of status messages containing: 'Gate_Drive_Power' with 
                               the current state of the power supply for the power stage.
                               In case of a error only the 'Error' element will be returned.
        """        
        status = {}
        success, msg =  self._send_command(f"SYST:GDPOW?", resp_qualifier="#GD ")
        if success:
            status['Gate_Drive_Power'] = bool(int(msg.replace("#GD ", "")))
        else:
            status['Error'] = msg

        return success, status
    
    def control_heating_power_stage(self, enable:bool) -> tuple[bool, dict]:
        """Controls the heating powerstage to switch the heating current for the heated JUT.
        This parameter is locked during a normal measurement and can only be written while 
        the measurement is stopped. In Test-Mode the parameter can be changed on the fly.

        Args:
            enable (bool): True enables the powerstage.

        Returns:
            tuple[bool, dict]: True when executed with success, otherwise False. 
                               Dictionary of status messages containing: 'Heating_Power_stage' with 
                               the current state of the power stage.
                               In case of a error only the 'Error' element will be returned.
        """    
        status = {}
        success, msg =  self._send_command(f"SYST:POWER {enable}", resp_qualifier="#PWSTG ")
        if success:
            status['Heating_Power_Stage'] = bool(int(msg.replace("#PWSTG ", "")))
        else:
            status['Error'] = msg

        return success, status

    def get_heating_power_stage(self) -> tuple[bool, dict]:
        """Read the current state of the power stage from the uTTA device.

        Returns:
            tuple[bool, dict]: True when executed with success, otherwise False. 
                               Dictionary of status messages containing: 'Heating_Power_stage' with 
                               the current state of the power stage.
                               In case of a error only the 'Error' element will be returned.
        """        
        status = {}
        success, msg =  self._send_command(f"SYST:POWER?", resp_qualifier="#PWSTG ")
        if success:
            status['Heating_Power_Stage'] = bool(int(msg.replace("#PWSTG ", "")))
        else:
            status['Error'] = msg

        return success, status
    
    def get_gate_driver_power_good(self) -> tuple[bool, dict]:
        """Read the current state of the power good signal from the uTTA device.

        Returns:
            tuple[bool, dict]: True when executed with success, otherwise False. 
                               Dictionary of status messages containing: 'Gate_Driver_Power_Good' with 
                               the power good signal of the power stage
                               In case of a error only the 'Error' element will be returned.
        """        
        status = {}
        success, msg =  self._send_command(f"SYST:PWUV?", resp_qualifier="#UVLO ")
        if success:
            status['Gate_Driver_Power_Good'] = bool(int(msg.replace("#UVLO ", "")))
        else:
            status['Error'] = msg

        return success, status

    def set_console_sample_rate(self, sample_rate:float) -> tuple[bool, dict]:
        """Set the sample rate the device returns measurement values during the TSP calibration measurement

        Args:
            sample_rate (float): Sets the sample rate in a range from 0.4 S/s to 40S/s

        Returns:
            tuple[bool, dict]: True when executed with success, otherwise False. 
                               Dictionary of status messages containing: 
                               'Console_Sample_Rate' with sample rate in Samples per second.
                               In case of a error only the 'Error' element will be returned.
        """        
        status = {}

        sr = int((1/sample_rate) *1000)

        success, msg =  self._send_command(f"SYST:RATE {sr}", resp_qualifier="#CSR ")
        if success:
            ret_sr = int(msg.replace("#CSR ", ""))
            status["Console_Sample_Rate"] = 1.0 / float(ret_sr / 1000)
        else:
            status['Error'] = msg

        return success, status


if __name__ == "__main__":

    # list_serial_ports(vid="0483", name="STLink")

    # utta_dev = uTTA_Serial_Communication(port='COM3')
    success = False
    msg = None
    # success, msg = utta_dev.identify_instrument()
    # print(f"Status: {msg}")
    # success, msg = utta_dev.reset_instrument()
    # msg = utta_dev.get_system_clock()
    # utta_dev.sync_system_time()
    # success, msg = utta_dev.set_cooling_time(1000)
    # success, msg = utta_dev.set_preheating_time(1000)
    # success, msg = utta_dev.set_heating_time(1000)
    # msg = utta_dev.write_calibration_file(os.path.abspath(r'..\..\060_Example_Measurement_Data\Calibration\20250505_SN001_Calibration.ucf'))
    # success, msg = utta_dev.get_time_settings()
    # success, msg = utta_dev.set_dut_name("TEST2fdgdfgdfgdfgdfg")

    # dev_cal_data, dev_meta_data ,utta_tsp_cal ,utta_tc_cal = udi.read_calfile2dict(os.path.abspath(r'..\..\060_Example_Measurement_Data\Calibration\20250505_SN001_Calibration.ucf') # type: ignore
    # success, msg = utta_dev.set_ch_description(1, "BUZ11_Test", utta_tsp_cal["$CHAN_BUZ11"])
    # success, msg = utta_dev.read_directory('/')
    # success, msg = utta_dev.get_system_calibration()
    
    # success, msg = utta_dev.get_system_error_status()
    # success, msg = utta_dev.get_system_status()

    # success, msg = utta_dev.set_offset_voltage(0, -0.3)
    # success, msg = utta_dev.set_sense_current(0, 0.0001)

    # success, msg = utta_dev.set_mode(scpi_consts.SystemModes.TEST)
    # success, msg = utta_dev.set_pga_gain(3, scpi_consts.PGA_GainSetModes.Cooling)
    # success, msg = utta_dev.get_pga_gain()
    # success, msg = utta_dev.download_file(file_name="/test3.umf")
    # success, msg = utta_dev.enable_ext_power_supply(False)
    # success, msg = utta_dev.get_ext_power_supply()
    # success, msg = utta_dev.enable_gate_driver_power(False)
    # time.sleep(0.05)
    # success, msg = utta_dev.get_gate_driver_power()
    # success, msg = utta_dev.enable_heating_power_stage(True)
    # time.sleep(0.05)
    # success, msg = utta_dev.get_heating_power_stage()
    # success, msg = utta_dev.get_gate_driver_power_good()
    # success, msg = utta_dev.enable_gate_driver_power(False)
    # success, msg = utta_dev.enable_heating_power_stage(False)
    # success, msg = utta_dev.set_console_sample_rate(10.0)

    # success, msg = utta_dev.download_file_v2(file_name="/test3.umf")
    # testname = "Test12"
    # success, msg = utta_dev.set_dut_name(f"{testname}")
    # success, msg = utta_dev.set_cooling_time(60)
    # success, msg = utta_dev.set_preheating_time(60)
    # success, msg = utta_dev.set_heating_time(60)
    # dev_cal_data, dev_meta_data ,utta_tsp_cal ,utta_tc_cal = udi.read_calfile2dict(os.path.abspath(r'..\..\060_Example_Measurement_Data\Calibration\20250505_SN001_Calibration.ucf') # type: ignore
 
    # success, msg = utta_dev.set_ch_description(1, "IRFZ44N_M", utta_tsp_cal["$CHAN_IRFZ44N_M"])
    # success, msg = utta_dev.set_ch_description(2, "IRFZ44N_L", utta_tsp_cal["$CHAN_IRFZ44N_L"])
    # success, msg = utta_dev.set_ch_description(3, "IRFZ44N_R", utta_tsp_cal["$CHAN_IRFZ44N_R"])

    # success, msg = utta_dev.set_measure(action=utta_dev.MeasureAction.START)

    # print(f"Status: {success}, {msg}")

    # while True:

    #     new_data, data = utta_dev.get_measurement_data()
    #     if new_data:
    #         print(data.replace("#M;", ""))
        
    #     if utta_dev.check_measurement_complete():
    #         while True:
    #             new_data, data = utta_dev.get_measurement_data()
    #             if new_data:
    #                 print(data.replace("#M;", ""))
    #             else:
    #                 break
    #         break

    #     time.sleep(0.05)
    
    # time.sleep(5)
    # success, msg = utta_dev.download_file(file_name=f"{testname}.umf")
    
    # filename = os.path.abspath(r'..\..\060_Example_Measurement_Data\Calibration\cal_test.ucf')
    # success, msg = utta_dev.upload_file(filename)
    print(f"Status: {success}, {msg}")