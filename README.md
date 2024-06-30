# uTTA - Micro Thermal Transient Analyzer
## What's this TTA stuff anyhow?

TTA (Thermal Transient Analysis) is a technique to retrieve the thermal impedance model of a cooling path by measuring its thermal step response.
This method was detailed specified in JESD 51-14 and is briefly descriped in the following tutorial:
[THERMINIC 20005 Tutorial](https://therminic.org/therminic2005/APoppe_Tutorial.pdf)

Ideally after performing the measurement you should be able to transform the measured data into a so called thermal impedance curve. This curve can be found in almost every datasheet of any power semiconductor. In a nutshell out of a thermal impedance curve the user can read the thermal resistance which applies to the device when a rectangular power pulse of the time x is applied. From this thermal resistance, in combination with the dissipated power the user can calculate the junction temperature of the power semiconductor at the end of the rectangular pulse. This only works as long as the power pulse is short enough to not reach the thermal boundaries of the power semiconductor. As soon as the thermal boundaries of the power semiconductor are reached a dedicated thermal impedance curve of your specific cooling path is needed. 
Nexperia released a very interesting application note on this topic: [Nexperia AN11156](https://assets.nexperia.com/documents/application-note/AN11156.pdf)

When applying non rectangular power pulses things get a little more complicated. For a rough approximation the extended rectangular is ok but it takes a lot of work.
If you want to do a thermal simulation all these graphs help you exactly zero. For thermal simulation the "easiest" way is to model the thermal cooling path by using a number of RC-circuits to resemble the heating and cooling behaviour. Again Nexperia released an application note on this topic: [Nexperia AN11261](https://assets.nexperia.com/documents/application-note/AN11261.pdf)

But how do you get these RC-Models from a power semiconductor including its heatsink?? Here the hassle really begins....
For a MOSFET you might get thermal models, but most of these are often only provided as encrypted SPICE models. Here again Nexperia is one of the few suppliers which offers sometimes thermal equivalent RC-models (some as Foster model, some as Cauer model). But for the heatsink you might only get a static thermal resistance, nothing more.

## How to perfom these measurements?
### The proper way
To measure thermal transients needed to perform the analysis a specialized measurement system is needed. This system is called T3ster and was developed by MicReD (which was later sold to Siemens).
This system costs enormous amounts of money (high 5 digit to 6 digit €). That's why I decided to try and build my own little system for private educational purposes.


### My own little Thermal Transient Analyzer (uTTA)
uTTA started off as a pasttime project during short-time work in the first COVID lockdown. During this time I was playing around with various kinds of power electronics and always faced the  same problems... 
How long can I dissipate this or that power dissipation in a MOSFET until I read a critical temperature?


### Target Picture
The following points are my target picture for this little project.
+ [x] Build a measurment hardware which is capable to perform thermal impedance measurements on one channel, whereby it should be able to monitor at least 2 further channels for doing thermal coupling analysis in the future.
+ [x] Build a software toolkit to postprocess measurement data to obtain thermal impedance curves (Z<sub>th</sub>-curves).
+ [x] Add functionalities for thermal coupling measurement between adjacent semiconductors.
+ [ ] Software tools for the calibration of the junction.
+ [x] Software tools for the calibration of the hardware itself.
+ [ ] Ability to calculate the time constant spectra of the Z<sub>th</sub>-curve via the NID method (either the "classical" methode by FFT deconvolution, or by using the bayesian method).
+ [ ] Obtain RC-thermal equivalent models from the time constant spectrum.


### Design Requirements
The device shall...
+ ...be easy to use.
+ ...be cheap and easy to build. Target: 150€ for all components incl. PCB.
+ ...only use off the shelf compontents, no hard to get or unobtainium parts.
+ ...include the switch for the heating current, which shall be able to handle um to 30A DC.
+ ...include a few thermocouple temperature sensor (Type K) to measure temperatures of interest at low speed (<5 Samples/s).
+ ...be able to measure  the JUT (Junction under Test) and 2 additional junctions for monitoring (thermal coupling).
+ ...shall provide different gain settings for the JUT monitor to get a good ADC resolution during the measurement.
+ ...provide a sample fast after shut off of the heating current of at least 1MS/s.
+ ...automatically handle a method to reduce the sampling rate after the transient to generate less useless data.
+ ...store all data within a built-in memory.
+ ...be controlled via a PC with some GUI which is easy to use.

# The current design
The current design consists of 3 PCBs which are stacked on top of each other. This stacked design was chosen to thermally decouple the power part from the measurement part.

![uTTA_System_Overview](https://github.com/wtronics/uTTA_private/assets/169440509/349de40f-0f6b-4d72-b7f7-e29c1427363e)


### The power PCB
This is the PCB at the bottom of the stack. It holds all the parts which are somehow related to power. Therefore on there is the overall power supply for the whole system. The system is fed by a bipolar power supply which should be able to deliver +/-12V with max. 120mA. In addition on the power PCB there is the main heating current switch and the heating current measurement which is used to switch and measure the heating current trough the JUT. Last but not least the power PCB holds a CR2032 backup battery which is used to run the RTC of the microcontroller.

![uTTA_Power_PCB_Overview1](https://github.com/wtronics/uTTA/assets/169440509/389ed171-3da6-4c48-be30-57c26e5d8b67)


### The Microcontroller PCB
This PCB is an off the shelf STM32F303RE Nucleo-64 Board. It is a little modified in terms of jumper settings. 

TODO: Document jumper settings of the Nucleo-Board

### The measure PCB
The top most PCB hold everything which is related to measurement. On this PCB there is the Offset voltage reference generator which provides a common offset voltage for all 4 Montior channels. Then there are 4 so called monitor channels. These channels provide a measurement current of ~1mA to each body diode and sense the voltage drop across the body diode. This voltage drop if amplified and offset with the voltage from the offset generator. Afterwards it is fed into the microcontrollers ADC. In Addition to the monitor channels there are 4 thermocouple transducer ICs MAX6675 to directly convert thermocouple values into temperatures. Finally there's the FLASH memory on the PCB which is used to save the measurement data during the measurement.

![uTTA_Power_PCB_Overview](https://github.com/wtronics/uTTA/assets/169440509/c7caf485-0921-4115-a7b5-6a46c6df0f11)


## How the measurement works
![image](https://github.com/wtronics/uTTA_private/assets/169440509/00a154a3-48e4-46bb-b495-6e1eae6e8ec8)
### Pre-Heating Phase
The whole measurement starts with a so called pre-heating phase. The pre-heating phase is intended to measure the initial voltage drops of the junctions under test (JUT). This is needed to be able to judge after the measurment if the JUTs have cooled completely to thermal equilibrium. During the pre-heating phase the sample rate on all channels is reduced to its lowest setting, which is a sampling period of 65536µs or ~15.26 Samples/s. Furthermore the programmable gain stage of the driven JUT is set to its initial setting (higher gain).

### Heating Phase
In the heating phasse the uTTA switches on the heating current switch to enable external power supply which provides the heating current for the DUT. In theory you should be able to use any power supply with current limit you have on hand. Output voltage requirements may depend a little on your specific setup. My setup always worked at ~3V with a heating current of ~10-12A, whereby the wires between uTTA and DUT were almost 2 metres long. In the heating phase uTTA switches the PGA into the preset setting (typically lower gain) to be able to measure the diode voltage while the heating current is running through the JUT. The diode voltage at the end of the heating phase is important to be able to calculate the dissipated power in the JUT. During the whole phase the sampling rate is still at its lowest setting because the data during heating do not provide much valuable content. At the end of the heating phase uTTA does multiple things in very short succesion.
1. Switch the PGA back to its higher gain setting to have the full measure range during the coming cooling phase
2. Set the ADC sampling rate to maximum speed. This means a sample rate of 2MS/s per channel. The samples are taken simultaneously on all 4 channels (because the STM32 has 4 built in ADCs).
3. Switch off the heating current switch and cut off the heating current.

### Cooling Phase

With these settings done the heating current through the device is cut really fast (~1-2µs) and all the inductive energy is dissipated in the Freewheeling network in parallel to the JUT (on the uTTA power PCB). While the current is freewheeling the microcontroller is continuously sampling at 2MS/s. After 250 samples the ADC halfes its sampling rate to 1MS/s, and after another 250Samples to 500kS/s. This process of taking 250samples and reducing the sample rate is done until the minimum sample rate of ~15.26 Samples/s is reached. From there the sampling continiues until the preset measurement time is reached. As the correct timing is extremely cricuial to the whole process the sampling is controlled by an internal timer which is set to these sampling rates. The change of sampling rates is performed by the timers preload registers which are automatically reloaded as soon as 250 samples were generated.

# Measurement postprocessing
## Measurement data retrieval

All measurement values of the ADC are transfered via DMA into a circular buffer array with a length of 5000 samples. From there the values are taken in blocks of 250 samples, transformed into a human readable format and transferred into the flash memory. As soon as the measurement is completed the user can transfer these measurement data files onto the PC via the serial port. For this purpose a LabView GUI was built to ease up the transfer process. After the transfer you will get a measurement file with the file extension *.t3r. This file extension was borrowed from the T3STER system, but is __NOT__ compatible with any of these systems.

![uTTA_GetFileUI](https://github.com/wtronics/uTTA_private/assets/169440509/9dfc242e-9216-414c-85aa-31bac8ef42d5)

## The measurement data file

As said before the measurement file has a *.t3r file extension to give it a unique name. Nevertheless this is still just a plain text file you can open with any text editor.

### File Header

Each measurement file starts with a file header which includes general information and settings which are needed for the postprocessing. All values are separated by a semicolon (the german delimiter for CSV-files).

![T3R_FileStructureHeader](https://github.com/wtronics/uTTA_private/assets/169440509/e03449df-1a28-4713-881e-e86667506e4b)

#### File Version
  The first line always indicates the file version. At the moment this should be version 2.2. Earlier file versions contained less information

#### CH_ Name
The following three lines always define a set of parameters for the measurement channels:
+ The symbolic name of the channel. This is intedend to ease up the postprocessing process. Especially when you do a lot of measurements.
+ $JUT_{Offset}$: The offset voltage of the diode voltage to temperature conversion line in µV. This value is not used by anything and can therefore be set to 0. The postprocessing function simply does a difference temperature measurement, therefore an accurate offset is not needed.
+ $JUT_{LinearGain}$: The linear portion of the voltage to temperature conversion slope in µV/K.
+ $JUT_{QuadraticGain}$:The quadratic portion of the voltage to temperature conversion slow in µV/K<sup>2</sup>. This value is currently not used and can therefore be set to 0.

For conversion of the measured voltage to a temperature the postprocessing function does the following calculation: $\frac{U_{JUT.cold} + JUT_{Offset}}{JUT_{LinearGain}}$

#### StartTime
Contains the start time of the measurement. Sometimes it's helpful to know when you started your measurement (especially when you're debugging).

#### StartDate
The date when the measurement was performed in DD.MM.YYYY format.

#### T<sub>samp,fast</sub>
Is the setting of the fast sample rate which is used at the start of the cooling section. This cryptic value can be converted to Samples per second with the following formula:
$\frac{8 MHz}{T_{samp,fast}}$

#### T<sub>samp,low</sub>
Is the setting of the lowest sample rate which is used most of the measurement time. This cryptic value can be converted to Samples per second with the following formula:
$\frac{8 MHz}{T_{samp,low}}$

#### Samples/Decade ($N_{SamplesDecade}$)
The name might be a bit misleading. It is not a decade but the length of a sampling block. The name is a historical choice I didn't bother to change.

#### Max. Divider
Is a slightly redundant value to T<sub>samp,low</sub>. This value basically describe how many times the sample time is halfed at the beginning of the cooling section. Therefore T<sub>samp,low</sub> can be calculated from T<sub>samp,fast</sub> with the following formula:
$T_{samp,low} = T_{samp,fast} * 2^{MaxDivider}$

#### T_Preheat
This value represents the preheating time used for the measurement in seconds. Please note that this value might not be precisely refleceted in the measurement as the internal state machine switched only at the beginning of a new block. Therefore a skew between the setting and the real measurement of $T_{samp.low}*N_{SamplesDecade}$ might occur.

#### T_Heat
This value represents the heating time used for the measurement in seconds. Please note that this value might not be precisely refleceted in the measurement as the internal state machine switched only at the beginning of a new block. Therefore a skew between the setting and the real measurement of $T_{samp.low}*N_{SamplesDecade}$ might occur.

#### T_Cool
This value represents the cooling time used for the measurement in seconds. Please note that this value might not be precisely refleceted in the measurement as the internal state machine switched only at the beginning of a new block. Therefore a skew between the setting and the real measurement of $T_{samp.low}*N_{SamplesDecade}$ might occur.

#### ADC1;ADC2;ADC3;ADC4
This is the final line of the file header. After this line the measurement data block starts.
### Measurement Data

![T3R_FileStructureNewBlock](https://github.com/wtronics/uTTA_private/assets/169440509/05b67c7d-082d-40f1-b809-1e404dfec69a)


#### #T lines
Lines starting with #T indicate a measurement data set from the type K thermocouples. After this prefix there are 4 values reflecting the 4 type K thermocouples. The values given are in tens of degrees Celsius, thus you need to divide this value by 10.

#### #B lines
Lines starting with #B indicate the start of a new block. After this prefix there is the block number which is continiuously counted up to the end of the measurement. In theory you don't need this tag because with complete data (without data loss) there shouldn't be the need for it. In practice these lines have proven usefull while debugging, therefore I kept them in.

#### #P lines
Lines starting with #P indicated the current gain configuration of the programmable gain amplifier. This is needed for the postprocessing to know which calibration factors need to be applied to channel 1.

#### Lines with raw numbers
All lines with raw numbers are raw ADC measurement values. The measurement values are not scaled within the measurement system, this is done at the postprocessing stage.

### File Footer

![T3R_FileStructureFooter](https://github.com/wtronics/uTTA_private/assets/169440509/1f4f2d4f-655f-4a46-af9b-c4edf30be552)


#### Cooling Start Block
This line is a helping line for the postprocessing software. As the exact number of blocks from start of the measurement to the start of the cooling phase might vary due to afforementioned timing inaccuacies an indicator was needed to find the first block of the cooling section more easily.

#### Total Blocks
This value reflects the total number of blocks generated during the measurement. 

## Measurement data postprocessing

Postprocessing of the measurements is done in Python (but there is also a very crusty LabVIEW GUI if someone likes :P ). 
At the momment there is no nice Python GUI. It's just a little script which creates a figure via matplotlib. 
By running the file "uTTA_Postprocess_Measurement.py" you will get these plots.

![DUT_Measurement_Graph](https://github.com/wtronics/uTTA_private/assets/169440509/20d022ce-bf6a-4d50-aba3-7b3a0e97c4fa)

### What do you see in these plots?
+ Let's start at the top left. This plot shows the change of the JUT voltages over the whole measurement period. As previously described the heated JUT jumpos to a significantly higher voltage during heating, due to the high heating current.
+ Right to the JUT voltages you can see the measured heating current. This graph has little information content. It's just there to verify nothing mysterious happend during the measurement.
+ In the second line you can see the same measurement data as above, whereas the preheating and heating section were cut off. The JUT voltages show the electrical transient which is created by the junction capacitance and the wire inductance. The heating current should ideally go to zero, but it seems like we can observe the cooling of the differential amplifier in this graph.
+ The third row on the left depicts the converted temperatures from the JUT scaling factors. The curve of the heated JUT is extended furhter to the switch off by using the interpolation formula. For the other two channels this is currently not implemented.
+ Third row on the right shows the measured values of the thermocouples. At the moment this plot is not scaled to the same timebase as the rest of the measurement data.
+ Last row on the least depicts the calculated thermal impedance curve. You can clearly see where the interpolation curve ends and where real measurement start.
+ Last row on the right show the coupling impedances between the heated JUT and the monitored JUTs.

In addition to the figure two files are created. The first one is a text file with all the scaled diode voltages of the whole cooling section.
The second file has the extension *.t3i (Don't ask, I forgot why). This  file contains intermediate results which can be used by the "uTTA_FFT_Deconvolution.py" script for further processing.

## ToDo
- [ ] Document jumper settings of the Nucleo-Board
- [x] Build calibration GUI for uTTA
- [ ] Build calibration GUI for DUT scaling factors

## Possible improvements for future designs
- [ ] More gain steps for diode voltage measurement
- [ ] Software adjustable offset control (DAC)
- [ ] Software adjustable measure current (maybe enhanced Howland current sources with DAC?)
- [ ] Removal of the Nucleo Board and replacement with a own development. (Improvements: Get rid of all these connectors, improve signal integrity, improve ADC reference voltage, maybe even dedicated USB interface not just throught the ST-Link.

## Design choices

I know this system is far from perfect. As said previously this started as a private hobby project during the COVID crisis as as originally meant to be a quick and dirty project. I never imagined that it would take me over 4 years to come this far. Somehow the whole topic hooked on, but due to private reasons I never had much time to intensively work on it. Over time many things changed in the hardware and software and many decissions may seem to be a bit crude for the external viewer. Therefore I will give you a little bit of a reasoning why some things are like you see them here:
+ Why are the measurement data stored in a flash memory? You could simply stream the data via serial interface and log them on your PC.
  + The serial port is set to 250kBaud and therefore is not capable to transmit all the sampled values during the phases of really fast sampling. Furthermore there is not enough RAM to buffer all the data and send it out afterwards. Therefore I had to use an external memory which is capable of absorbing all the incoming samples for later read out. At the beginning I used an mircro SD card with FATfs for this task, but SD cards tend to wear out really quick, that's why a Flash memory with littleFS is used.
+ Why do you use only one switchable amplfier? Shouldn't there be a switchable amplifier for each channel?
  + The switchable amplifier is reserved for the channel which is heated by the heating current. As the diode voltage will be by far higher during heating due to the heating current, the amplifier needs to reduce its gain to be still in a measureable range.
  + The other channels "just" monitor the diodes with the low measurement current, thus there is no need to switch gains. The measurement range of these channels should be fine for pretty much every standard silicon diode or MOSFET body diode.
+ Why do you use LabVIEW for your GUI?
  + Because I also use it in my day time job, where I have the role of an "lazy" senior hardware developer :). There software for testing needs to be build fast and that's whats LabVIEW good for.
  + I know there's a lot of people which don't like LabVIEW, but for creating an easy GUI its my number one choice (Its fast, easy and you don't have to mess around with TKinter libraries).

