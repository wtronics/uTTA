import serial
import serial.tools.list_ports
import threading
import queue
import time
from datetime import datetime
import re
import os
import uTTA_data_import as udi
import uTTA_SCPI_Driver_Constants as scpi_consts



def list_serial_ports(pid=None, vid=None, name=None):
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
    print("+#" * 18 + " Serial Ports (COM & VCP) " + "+#" * 18)
    if not out_ports:
        print("No entries found.")
        return

    for p in out_ports:
        print(f"Port: {p['device']}")
        print(f"  Name:         {p['name']}")
        print(f"  Vendor    :   {p['manufacturer']}")
        print(f"  Hardware-ID:  {p['hwid']}")
        print("+#" * 49)

    return out_ports

class uTTA_Serial_Communication:
    def __init__(self, port:str, baudrate=250000):
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
        self.running = False
        self.ser.close()
   
    def _flush_received(self):
        with self.response_queue.mutex:
            self.response_queue.queue.clear()

    def _reader_loop(self):
        # reads permanently from the serial port and sorts data into matching queue

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

    def _send_command_async(self, cmd:str, resp_qualifier=None, timeout:float=2,  multiline_response:bool=False): 
        # Sends a command and does not wait for a response
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
        try:
            # wait for the specific answer from the reader thread
            response = str(self.response_queue.get(timeout=0.001))
            return self._validate_response(response)
        except queue.Empty:
            return False, ""

    def check_measurement_complete(self) -> bool:
        if self.measurement_running == scpi_consts.MeasureAction.START:
            return False
        return True
    
    def get_measurement_data(self) -> tuple[bool, str]:
        if not self.meas_data_queue.empty():
            return True, self.meas_data_queue.get()
        return False, ""

    def _send_command(self, cmd:str, resp_qualifier=None, timeout:float=2,  multiline_response:bool=False) -> tuple[bool, str]:
        # Sends a command and waits for the response
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
                return self._validate_response(response)
            except queue.Empty:
                return False,f"1.100 {self.error_codes["1.100"]}"
        else:
            return True, "No Query"

    def _validate_response(self, response:str) -> tuple[bool, str]:
        # validates the device response against the expected message
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

        success, msg = self._send_command("*IDN?", resp_qualifier=", uTTA, SN")
        if success:
            dev_sn = msg.split(", uTTA, SN")[1]
            dev_sn = dev_sn.split(",")[0]
            self.device_id = f"SN{dev_sn.strip()}"
            print(f"Device Serial Number: {self.device_id}")
        return success, msg

    def reset_instrument(self) -> tuple[bool, dict]:
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
        self._flush_received()
        success, msg =  self._send_command("SYST:CLOCK?", resp_qualifier="#TIME")
        if success:
            msg = msg.replace("#TIME ", "")
            date_time = datetime.strptime(msg, '%d.%m.%Y %H:%M:%S')
            return success, date_time
        return success, None
 
    def sync_system_time(self):
        success, utta_time = self.get_system_clock()
        system_time = datetime.now()
        if utta_time:
            d_time = abs(utta_time-system_time)

            print(f"System Time {system_time}, uTTA-Time {utta_time}, Difference {d_time.seconds}")

            if d_time.seconds >= 10:        # difference is larger than 1 Minute, therefore a synchronisation is done
                self.set_system_date(datetime.now())
                self.set_system_time(datetime.now())
    
    def set_system_time(self, sys_time:datetime) -> bool:
        success = False
        if sys_time:
            timestr = datetime.strftime(sys_time, "%H,%M,%S")
            success, msg =  self._send_command(f"SYST:CLOCK TIME,{timestr}")
        return success

    def set_system_date(self, sys_date:datetime) -> bool:
        success = False
        if sys_date:
            datestr = datetime.strftime(sys_date, "%d,%m,%Y")
            success, msg =  self._send_command(f"SYST:CLOCK DATE,{datestr}")
        return success

    def memory_speedtest(self) -> int:

        success, msg =  self._send_command(f"MEM:WRITE", resp_qualifier="Write took ", timeout=30)
        if success:
            msg = msg.replace("Write took ","").replace(" ms","")
            return int(msg)
        return -1

    def delete_file(self, file_name:str) -> bool:
        success = False

        if file_name:
            success, msg =  self._send_command(f"MEM:DEL  {file_name}", resp_qualifier="Deleted: ")
            if success:
                msg = msg.replace("Deleted: ", "")
        return success
    
    def write_calibration_file(self, file_name:str) -> bool:
        success = False

        if file_name.endswith(".ucf"):
            dev_cal_data, dev_meta_data ,utta_tsp_cal ,utta_tc_cal = udi.read_calfile2dict(file_name) # type: ignore
            
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
    
    def download_file(self,file_name:str=r'/') -> tuple[bool, str]:

        success, msg =  self._send_command(f"MEM:READ {file_name}", resp_qualifier="Read took ", timeout=300, multiline_response=True)
        if success:
            msg = self.process_downloaded_file(msg)
        return success, msg
    
    def download_file_v2(self,file_name:str=r'/'):

        self._send_command_async(f"MEM:READ {file_name}", resp_qualifier="Read took ", timeout=300, multiline_response=True)
        # Example implementation of a possible read out of the progress
        # while True:
        #     success, msg = self._check_async_command_complete()
        #     if success:
        #         return success, self.process_downloaded_file(msg)     
        #     else:
        #         print(f"Number of lines read: {self.line_count}")
        #         time.sleep(0.2)
    
    def process_downloaded_file(self, fil_data:str) -> str:
        lines = fil_data.splitlines()
        del lines[0]
        del lines[-1]
        msg = '\n'.join(lines)
        return msg

    def upload_file(self, file_path:str) -> tuple[bool, dict]:
        status = {}
        success = False
        if file_path:
            file_name = os.path.basename(file_path)

            with open(file_path, 'r') as send_file:
                file_content = send_file.readlines()
            
            success, status = self._upload_file(file_name, file_content)
        
        return success, status

    def _upload_file(self,file_name:str, file_contents:list, interline_delay:float=0.02) -> tuple[bool, dict]:

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
        success = False
        status = {}
        if t_cool >= 0:
            success, msg =  self._send_command(f"MEAS:TIM:COOL {t_cool*1000}", resp_qualifier="MEAS:TIM ")
            if success:
                status = self._parse_timing_response(msg)
            else:
                status["Error"] = msg
        return success, status
    
    def set_heating_time(self, t_heat:int) -> tuple[bool, dict]:
        success = False
        status = {}
        if t_heat >= 0:
            success, msg =  self._send_command(f"MEAS:TIM:HEAT {t_heat*1000}", resp_qualifier="MEAS:TIM ")
            if success:
                status = self._parse_timing_response(msg)
            else:
                status["Error"] = msg
        return success, status
    
    def set_preheating_time(self, t_preheat:int) -> tuple[bool, dict]:
        success = False
        status = {}
        if t_preheat >= 0:
            success, msg =  self._send_command(f"MEAS:TIM:PRE {t_preheat*1000}", resp_qualifier="MEAS:TIM ")
            if success:
                status = self._parse_timing_response(msg)
            else:
                status["Error"] = msg
        return success, status

    def get_time_settings(self) -> tuple[bool, dict]:
        status = {}
        success, msg =  self._send_command(f"MEAS:TIME?", resp_qualifier="MEAS:TIM ")
        if success:
            status = self._parse_timing_response(msg)
        else:
            status["Error"] = msg
        return success, status
    
    def _parse_timing_response(self, time_resp:str) -> dict:
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
        success = False
        status = {}
        max_chars = 16
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
        success = False
        msg = "Parameter Error"
        key_names = ["Offset", "LinGain", "QuadGain", "CalStatus"]
        ret_params:dict = {}

        for k in key_names:
            if not k in ch_cal:
                ret_params["Error"]  = "Missing parameter in calibration " + k
                return success, ret_params
            
        if 1 <= meas_ch_no <= 4:
            max_chars = 16
            name = (ch_name[:max_chars]) if len(ch_name) > max_chars else ch_name   # limit string to length
            name = re.sub("[^a-zA-Z0-9]", '_', name)
            scale = 1000000
            #print(f"MEAS:CHDESC {meas_ch_no},{name},{ch_cal["Offset"]*scale},{ch_cal["LinGain"]*scale},{ch_cal["QuadGain"]*scale},{ch_cal["CalStatus"]}")
            success, msg =  self._send_command(f"MEAS:CHDESC {meas_ch_no},{name},{ch_cal["Offset"]*scale},{ch_cal["LinGain"]*scale},{ch_cal["QuadGain"]*scale},{ch_cal["CalStatus"]}", resp_qualifier="#CH ")
            
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
        if action == scpi_consts.MeasureAction.START:
            return  self._send_command(f"MEAS:START", resp_qualifier="OK")
        elif action == scpi_consts.MeasureAction.STOP:
            return  self._send_command(f"MEAS:STOP", resp_qualifier="Measurement completed!", timeout=15)

    def set_mode(self, mode:scpi_consts.SystemModes) -> tuple[bool, str]:
       
        return  self._send_command(f"SYST:MODE {mode.name}", resp_qualifier="OK")
      
    def get_system_calibration(self) -> tuple[bool, dict]:
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
    
    def set_offset_voltage(self, channel:int, voltage:float) -> tuple[bool, str]:
        ret_val = 0
        success, msg =  self._send_command(f"MEAS:SET VOFF,{channel},{voltage*1000}", resp_qualifier="OK ")
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
        ret_val = 0
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
        measure_gains = {}
        if mode == scpi_consts.PGA_GainSetModes.ALL:
            success, msg =  self._send_command(f"SYST:GAIN {gain}", resp_qualifier="#PGA ")
        else:
            success, msg =  self._send_command(f"SYST:GAIN {mode.name.upper()},{gain}", resp_qualifier="#PGA ")
        if success:
            measure_gains = self._parse_pga_gains(msg)
        else:
            measure_gains['Error'] = msg

        return success, measure_gains
    
    def get_pga_gain(self) -> tuple[bool, dict]:
        measure_gains = {}
        success, msg =  self._send_command(f"SYST:GAIN?", resp_qualifier="#PGA ")
        if success:
            measure_gains = self._parse_pga_gains(msg)
        else:
            measure_gains['Error'] = msg

        return success, measure_gains
    
    def _parse_pga_gains(self, msg:str) -> dict:
        measure_gains = {}
        gains = msg.replace("#PGA ", "").strip().split(";")
        if len(gains)==3:
            measure_gains = {"Set": int(gains[0]),
                            "Cooling": int(gains[1]),
                            "Heating": int(gains[2]) }
        else:
            measure_gains['Error'] = "Too few parameters returned"
        return measure_gains

    def enable_ext_power_supply(self, enable:bool) -> tuple[bool, dict]:
        status = {}
        success, msg =  self._send_command(f"SYST:PSU {enable}", resp_qualifier="#PSU ")
        if success:
            status['PSU'] = bool(int(msg.replace("#PSU ", "")))
        else:
            status['Error'] = msg

        return success, status

    def get_ext_power_supply(self) -> tuple[bool, dict]:
        status = {}
        success, msg =  self._send_command(f"SYST:PSU?", resp_qualifier="#PSU ")
        if success:
            status['PSU'] = bool(int(msg.replace("#PSU ", "")))
        else:
            status['Error'] = msg

        return success, status

    def enable_gate_driver_power(self, enable:bool) -> tuple[bool, dict]:
        status = {}
        success, msg =  self._send_command(f"SYST:GDPOW {enable}", resp_qualifier="#GD ")
        if success:
            status['Gate_Drive_Power'] = bool(int(msg.replace("#GD ", "")))
        else:
            status['Error'] = msg

        return success, status
    
    def get_gate_driver_power(self) -> tuple[bool, dict]:
        status = {}
        success, msg =  self._send_command(f"SYST:GDPOW?", resp_qualifier="#GD ")
        if success:
            status['Gate_Drive_Power'] = bool(int(msg.replace("#GD ", "")))
        else:
            status['Error'] = msg

        return success, status
    
    def enable_heating_power_stage(self, enable:bool) -> tuple[bool, dict]:
        status = {}
        success, msg =  self._send_command(f"SYST:POWER {enable}", resp_qualifier="#PWSTG ")
        if success:
            status['Heating_Power_Stage'] = bool(int(msg.replace("#PWSTG ", "")))
        else:
            status['Error'] = msg

        return success, status

    def get_heating_power_stage(self) -> tuple[bool, dict]:
        status = {}
        success, msg =  self._send_command(f"SYST:POWER?", resp_qualifier="#PWSTG ")
        if success:
            status['Heating_Power_Stage'] = bool(int(msg.replace("#PWSTG ", "")))
        else:
            status['Error'] = msg

        return success, status
    
    def get_gate_driver_power_good(self) -> tuple[bool, dict]:
        status = {}
        success, msg =  self._send_command(f"SYST:PWUV?", resp_qualifier="#UVLO ")
        if success:
            status['Gate_Driver_Power_Good'] = bool(int(msg.replace("#UVLO ", "")))
        else:
            status['Error'] = msg

        return success, status

    def set_test_sample_rate(self, sample_rate:int) -> tuple[bool, dict]:
        status = {}

        success, msg =  self._send_command(f"SYST:RATE {sample_rate}", resp_qualifier="#CSR ")
        if success:
            status["Test_Sample_Rate"] = int(msg.replace("#CSR ", ""))
        else:
            status['Error'] = msg

        return success, status


if __name__ == "__main__":

    list_serial_ports(vid="0483", name="STLink")

    utta_dev = uTTA_Serial_Communication(port='COM3')
    success = False
    msg = None
    # success, msg = utta_dev.identify_instrument()
    # print(f"Status: {msg}")
    success, msg = utta_dev.reset_instrument()
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
    success, msg = utta_dev.read_directory('/')
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
    # success, msg = utta_dev.set_test_sample_rate(100)

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