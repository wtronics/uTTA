# Measurement postprocessing
## Measurement data retrieval

All measurement values of the ADC are transferred via DMA into a circular buffer array with a length of 5000 samples. From there the values are taken in blocks of 250 samples, transformed into a human readable format and transferred into the flash memory. As soon as the measurement is completed the user can transfer these measurement data files onto the PC via the serial port. For this purpose a LabView GUI was built to ease up the transfer process. After the transfer you will get a measurement file with the file extension *.t3r. This file extension was borrowed from the T3STER system, but is __NOT__ compatible with any of these systems.

![uTTA_GetFileUI](https://github.com/wtronics/uTTA_private/assets/169440509/9dfc242e-9216-414c-85aa-31bac8ef42d5)

## The measurement data file

As said before the measurement file has a *.t3r file extension to give it a unique name. Nevertheless, this is still just a plain text file you can open with any text editor.

### File Header

Each measurement file starts with a file header which includes general information and settings which are needed for the postprocessing. All values are separated by a semicolon (the German delimiter for CSV-files).

![T3R_FileStructureHeader](https://github.com/wtronics/uTTA_private/assets/169440509/e03449df-1a28-4713-881e-e86667506e4b)

#### File Version
  The first line always indicates the file version. At the moment this should be version 2.2. Earlier file versions contained less information

#### CH_ Name
The following three lines always define a set of parameters for the measurement channels:
+ The symbolic name of the channel. This is intended to ease up the postprocessing process. Especially when you do a lot of measurements.
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
Is a slightly redundant value to T<sub>samp,low</sub>. This value basically describe how many times the sample time is halved at the beginning of the cooling section. Therefore T<sub>samp,low</sub> can be calculated from T<sub>samp,fast</sub> with the following formula:
$T_{samp,low} = T_{samp,fast} * 2^{MaxDivider}$

#### T_Preheat
This value represents the preheating time used for the measurement in seconds. Please note that this value might not be precisely reflected in the measurement as the internal state machine switched only at the beginning of a new block. Therefore a skew between the setting and the real measurement of $T_{samp.low}*N_{SamplesDecade}$ might occur.

#### T_Heat
This value represents the heating time used for the measurement in seconds. Please note that this value might not be precisely reflected in the measurement as the internal state machine switched only at the beginning of a new block. Therefore a skew between the setting and the real measurement of $T_{samp.low}*N_{SamplesDecade}$ might occur.

#### T_Cool
This value represents the cooling time used for the measurement in seconds. Please note that this value might not be precisely reflected in the measurement as the internal state machine switched only at the beginning of a new block. Therefore a skew between the setting and the real measurement of $T_{samp.low}*N_{SamplesDecade}$ might occur.

#### ADC1;ADC2;ADC3;ADC4
This is the final line of the file header. After this line the measurement data block starts.
### Measurement Data

![T3R_FileStructureNewBlock](https://github.com/wtronics/uTTA_private/assets/169440509/05b67c7d-082d-40f1-b809-1e404dfec69a)


#### #T lines
Lines starting with #T indicate a measurement data set from the type K thermocouples. After this prefix there are 4 values reflecting the 4 type K thermocouples. The values given are in tens of degrees Celsius, thus you need to divide this value by 10.

#### #B lines
Lines starting with #B indicate the start of a new block. After this prefix there is the block number which is continuously counted up to the end of the measurement. In theory you don't need this tag because with complete data (without data loss) there shouldn't be the need for it. In practice these lines have proven useful while debugging, therefore I kept them in.

#### #P lines
Lines starting with #P indicated the current gain configuration of the programmable gain amplifier. This is needed for the postprocessing to know which calibration factors need to be applied to channel 1.

#### Lines with raw numbers
All lines with raw numbers are raw ADC measurement values. The measurement values are not scaled within the measurement system, this is done at the postprocessing stage.

### File Footer

![T3R_FileStructureFooter](https://github.com/wtronics/uTTA_private/assets/169440509/1f4f2d4f-655f-4a46-af9b-c4edf30be552)


#### Cooling Start Block
This line is a helping line for the postprocessing software. As the exact number of blocks from start of the measurement to the start of the cooling phase might vary due to aforementioned timing inaccuracies an indicator was needed to find the first block of the cooling section more easily.

#### Total Blocks
This value reflects the total number of blocks generated during the measurement. 

# Measurement data postprocessing
## Conversion from measurement data to Z<sub>th</sub>-Curves
Postprocessing of the measurements is done in Python (but there is also a very crusty LabVIEW GUI if someone likes :P ). 
Currently there is no nice Python GUI. It's just a little script which creates a figure via matplotlib. 
By running the file "uTTA_Postprocess_Measurement.py" you will get these plots.

![DUT_Measurement_Graph](https://github.com/wtronics/uTTA_private/assets/169440509/20d022ce-bf6a-4d50-aba3-7b3a0e97c4fa)

### What do you see in these plots?
+ Let's start at the top left. This plot shows the change of the JUT voltages over the whole measurement period. As previously described the heated JUT jumps to a significantly higher voltage during heating, due to the high heating current.
+ Right to the JUT voltages you can see the measured heating current. This graph has little information content. It's just there to verify nothing mysterious happened during the measurement.
+ In the second line you can see the same measurement data as above, whereas the preheating and heating section were cut off. The JUT voltages show the electrical transient which is created by the junction capacitance and the wire inductance. The heating current should ideally go to zero, but it seems like we can observe the cooling of the differential amplifier in this graph.
+ The third row on the left depicts the converted temperatures from the JUT scaling factors. The curve of the heated JUT is extended further to the switch off by using the interpolation formula. For the other two channels this is currently not implemented.
+ Third row on the right shows the measured values of the thermocouples. At the moment this plot is not scaled to the same time base as the rest of the measurement data.
+ Last row on the least depicts the calculated thermal impedance curve. You can clearly see where the interpolation curve ends and where real measurement start.
+ Last row on the right shows the coupling impedances between the heated JUT and the monitored JUTs.

In addition to the figure two files are created. The first one is a text file with all the scaled diode voltages of the whole cooling section.
The second file has the extension *.t3i (Don't ask, I forgot why). This file contains intermediate results which can be used by the "uTTA_FFT_Deconvolution.py" script for further processing.

## Conversion from Z<sub>th</sub>-Curves to time constant spectra
Here the real drama begins. In principle all the aforementioned documents contain the methods how to obtain the time constant spectrum, but all of them lack a few details which are vital for the correct function. 
In the following chapter I will try to give a summary of the process which is implemented right now. All steps are also descibed in [THERMINIC 20005 Tutorial, page 58.ff](https://therminic.org/therminic2005/APoppe_Tutorial.pdf), but some important details are missing.

1. After importing the *.t3i file the data is split into the timebase and the 3 calculated Zth curves and in the following steps only the Zth curve of the heated JUT is processed, all other channels are ignored for the moment. The imported measurement data still have the same sampling scheme as the original measurement data, therefore they are not evenly spaced (only within the blocks of 250 samples), but this is not dramatic as you will see in the next steps
2. As described the timebase needs to be logarithmic for the follwing steps. Therefore the imported timebase is converted with $z=ln(t)$. Nevertheless, this step has basically no fruitful impact, because the already unevenly spaced samples are now even more uneven.
3. To get the unevenly spaced samples into a format which can be processed later on, the samples need to be layed out on the logarithmic time axis with an even spacing. This is done by creating a new linear timebase with evenly spaced samples. The range of this timebase is $[min(z), max(z)]$ (I will call this axis the z-axis).
4. Now the unevenly spaced samples and its corresponding timebase can be interpolated to new samples onto the z-axis.
5. With this interpolated curve the derivative of the signal is calculated. This step will amplify the noise in the measurement drastically. 
6. After the derivation the curve curve needs to be modified for the FFT later on. Zero padding need to be added to the curve. This is necessary because the FFT always assumes a repetitve input signal. The signal isn't repetitve therefore, it needs to add the same amount of samples as zeros to the signal.
7. Before the deconvolution can be started two addtional curves need to be created.
   1. The weighing function $w_z(z)=e^{z-e^z}$
   2. The filter function $\frac{1}{e^{|\frac{|\Phi|-\Phi_0}{\rho}|}+1}$ (This is not mentioned in the THERMINIC Tutorial but here: [](https://diglib.tugraz.at/download.php?id=5cc8223dd3723&location=browse)
