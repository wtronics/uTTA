# uTTA - The  (µ) micro Thermal Transient Analyzer
## What's this TTA stuff anyhow?

TTA (Thermal Transient Analysis) is a technique to retrieve the thermal impedance model of a cooling path by measuring its thermal step response.
This method was detailed specified in JESD 51-14 and is briefly described in the following tutorial:
[Transient thermal measurements and thermal equivalent circuit models]([https://therminic.org/therminic2005/APoppe_Tutorial.pdf](https://www.infineon.com/dgdl/Infineon-Thermal_equivalent_circuit_models-ApplicationNotes-v01_02-EN.pdf?fileId=db3a30431a5c32f2011aa65358394dd2)) (Highly recommended!)

Ideally after performing the measurement, you should be able to transform the measured data into a so called thermal impedance curve. This curve can be found in almost every datasheet of any power semiconductor. In a nutshell out of a thermal impedance curve the user can read the thermal resistance which applies to the device when a rectangular power pulse of the time x is applied. From this thermal resistance, in combination with the dissipated power the user can calculate the junction temperature of the power semiconductor at the end of the rectangular pulse. This only works as long as the power pulse is short enough to not reach the thermal boundaries of the power semiconductor. As soon as the thermal boundaries of the power semiconductor are reached a dedicated thermal impedance curve of your specific cooling path is needed. 
Nexperia released a very interesting application note on this topic: [Nexperia AN11156](https://assets.nexperia.com/documents/application-note/AN11156.pdf)

When applying non rectangular power pulses things get a little more complicated. For a rough approximation the extended rectangular is ok but it takes a lot of work.
If you want to do a thermal simulation all these graphs help you exactly zero. For thermal simulation the "easiest" way is to model the thermal cooling path by using a number of RC-circuits to resemble the heating and cooling behavior. Again Nexperia released an application note on this topic: [Nexperia AN11261](https://assets.nexperia.com/documents/application-note/AN11261.pdf)

But how do you get these RC-Models from a power semiconductor including its heatsink?? Here the hassle really begins....
For a MOSFET you might get thermal models, but most of these are often only provided as encrypted SPICE models. Here again Nexperia is one of the few suppliers which offers sometimes thermal equivalent RC-models (some as Foster model, some as Cauer model). But for the heatsink you might only get a static thermal resistance, nothing more.

## How to perform these measurements?
### The proper way
To measure thermal transients needed to perform the analysis a specialized measurement system is needed. This system is called T3ster and was developed by MicReD (which was later sold to Siemens).
This system costs enormous amounts of money (high 5 to 6 digit €). That's why I decided to try and build my own little system for private and educational purposes.


### My own little Thermal Transient Analyzer (uTTA)
uTTA started off as a pastime project during short-time work in the first COVID lockdown. During this time, I was playing around with various kinds of power electronics and always faced the same problems... 
How long can I dissipate this or that power dissipation in a MOSFET until it reaches a critical temperature? As mentioned above there are various ways to accomplish this task. But all of them require you to know the thermal impedance curve of your specific hardware setup.


#### Target Picture
The following points are my target picture for this little project and what I achieved so far.
+ [x] Build a measurement hardware which is capable to perform thermal impedance measurements on one channel, whereby it should be able to monitor at least 2 further channels for doing thermal coupling analysis in the future.
+ [x] Build a software toolkit to postprocess measurement data to obtain thermal impedance curves (Z<sub>th</sub>-curves).
+ [x] Add functionalities for thermal coupling measurement between adjacent semiconductors.
+ [x] Software tools for the calibration of the hardware itself.
+ [ ] Ability to calculate the time constant spectra of the Z<sub>th</sub>-curve via the NID method (either the "classical" method by FFT deconvolution, or by using the Bayesian method).
+ [ ] Obtain RC-thermal equivalent models from the time constant spectrum.
+ [x] Software and hardware tools for the calibration of the junction.

#### Design Requirements
The device shall...
+ ...be easy to use.
+ ...be cheap and easy to build. Target: 150€ for all components incl. PCB.
+ ...only use off the shelf components, no hard to get or unobtanium parts.
+ ...include the switch for the heating current, which shall be able to handle up to 30A DC.
+ ...include a few thermocouple temperature sensor (Type K) to measure temperatures of interest at low speed (<5 Samples/s).
+ ...be able to measure the JUT (Junction under Test) and 2 additional junctions for monitoring (thermal coupling).
+ ...shall provide different gain settings for the JUT monitor to get a good ADC resolution during the measurement.
+ ...provide a sample fast after shut off of the heating current of at least 1MS/s.
+ ...automatically handle a method to reduce the sampling rate after the transient to generate less useless data.
+ ...store all data within a built-in memory.
+ ...be controlled via a PC with some GUI which is easy to use.

# The Implementation
## µTTA Hardware
This is how µTTA looks like (this is an older PCB version which has been modified to match the current µTTA hardware version. 
![Board_Stackup](https://github.com/user-attachments/assets/138ebe40-68f3-4df5-a533-04464e3c2e3f)

## The final test setup
Below you can see all the parts involved in the test setup. The JUT setup is placed next to the power supply. In a real setup this part will be placed within a still air chamber to minimize effects of uncontrolled ambient air circulation. Ideally this part should be placed on a temperature controlled coolplate, but this is something I will not build for my purposes.
![Test Setup](https://github.com/user-attachments/assets/3a8780f4-51e5-43f8-9253-6b1bf6234ee3)

## The JUT setup

Sadly I don't have a real world application test setup. Therefore I built a little setup which somehow looks like a real world setup. The setup contains 3 MOSFETs which I had lying around which are mounted onto the same heatsink. The devices are mounted with isolating glimmer and silicone pads, but to provide a return path for the sensing current of the monitored devices, the isolating washers were removed to connect the drains of the MOSFETs together. The Gate and Source of each MOSFET are shorted together to prevent spurious turn on by static charges. Additionally each MOSFET is connected to a coaxial sense cable for monitoring the forward voltage of the Body Diodes and to provide the sense current for each JUT. The heated junction is also connected to the wires which carry the heating current. These cables are special self made wires which are braided out ouf HF stranded wire. This was done to reduce the inductance of the wires. Furthermore the positive and negative wire are bundled into a braided insulation tube to keep the loop area between the wires as small as possible.
![JUT_on_Heatsink](https://github.com/user-attachments/assets/10768b4d-3334-4fc3-a089-28a2de61916c)


# ToDo
- [x] Build calibration GUI for uTTA.
- [x] Build calibration GUI for DUT scaling factors.
- [ ] Document jumper settings of the Nucleo-Board.
- [ ] Get the deconvolution to work.
- [ ] Calculate RC-Models from the time constant spectrum.
- [ ] Build a nice (non LabVIEW) GUI.

# Possible improvements for future designs
- [ ] More gain steps for diode voltage measurement.
- [x] Software adjustable offset control (DAC).
- [x] Software adjustable measure current (maybe enhanced Howland current sources with DAC?).
- [ ] Removal of the Nucleo Board and replacement with a own development. (Improvements: Get rid of all these connectors, improve signal integrity, improve ADC reference voltage, maybe even dedicated USB interface not just through the ST-Link.

## Design choices

I know this system is far from perfect. As said previously this started as a private hobby project during the COVID crisis as as originally meant to be a quick and dirty project. I never imagined that it would take me over 4 years to come this far. Somehow the whole topic hooked on, but due to private reasons I never had much time to intensively work on it. Over time many things changed in the hardware and software and many decisions may seem to be a bit crude for the external viewer. Therefore, I will give you a little bit of a reasoning why some things are like you see them here:
+ Why are the measurement data stored in a flash memory? You could simply stream the data via serial interface and log them on your PC.
  + The serial port is set to 250kBaud and therefore is not capable to transmit all the sampled values during the phases of really fast sampling. Furthermore, there is not enough RAM to buffer all the data and send it out afterwards. Therefore, I had to use an external memory which is capable of absorbing all the incoming samples for later read out. At the beginning I used an mircro SD card with FATfs for this task, but SD cards tend to wear out really quick, that's why a Flash memory with littleFS is used.
+ Why do you use only one switchable amplifier? Shouldn't there be a switchable amplifier for each channel?
  + The switchable amplifier is reserved for the channel which is heated by the heating current. As the diode voltage will be by far higher during heating due to the heating current, the amplifier needs to reduce its gain to be still in a measurable range.
  + The other channels "just" monitor the diodes with the low measurement current, thus there is no need to switch gains. The measurement range of these channels should be fine for pretty much every standard silicon diode or MOSFET body diode.
+ Why do you use LabVIEW for your GUI?
  + Because I also use it in my day time job, where I have the role of an "lazy" senior hardware developer :). There software for testing needs to be build fast and that's what’s LabVIEW good for.
  + I know there's a lot of people which don't like LabVIEW, but for creating an easy GUI it’s my number one choice (Its fast, easy and you don't have to mess around with TKinter libraries).
+ why do you use an external battery for the gate driver of the heating current switch? You could also use a power supply!
  + At the beginning I was in fact using another power supply for the gate driver. But I was constantly fighting with common mode issues, that's why I changed this part to a 9V or 12V battery which eliminated all problems completely. 
