# Theory of Operation
![image](https://github.com/user-attachments/assets/13192070-7060-41b5-80cc-b9c983e4eeda)

## Pre-Heating Phase
The whole measurement starts with a so-called pre-heating phase. The pre-heating phase is intended to measure the initial voltage drops of the junctions under test (JUT). This is needed to be able to judge after the measurement if the JUTs have cooled completely to thermal equilibrium. During the pre-heating phase the sample rate on all channels is reduced to its lowest setting, which is a sampling period of 65536µs or ~15.26 Samples/s. Furthermore, the programmable gain stage of the driven JUT is set to its initial setting (higher gain).

## Heating Phase
In the heating phase the uTTA switches on the heating current switch to enable external power supply which provides the heating current for the DUT. In theory you should be able to use any power supply with current limit you have on hand. Output voltage requirements may depend a little on your specific setup. My setup always worked at ~3V with a heating current of ~10-12A, whereby the wires between uTTA and DUT were almost 2 meters long. In the heating phase uTTA switches the PGA into the preset setting (typically lower gain) to be able to measure the diode voltage while the heating current is running through the JUT. The diode voltage at the end of the heating phase is important to be able to calculate the dissipated power in the JUT. During the whole phase the sampling rate is still at its lowest setting because the data during heating do not provide much valuable content. At the end of the heating phase uTTA does multiple things in very short succession.
1. Switch the PGA back to its higher gain setting to have the full measure range during the coming cooling phase
2. Set the ADC sampling rate to maximum speed. This means a sample rate of 2MS/s per channel. The samples are taken simultaneously on all 4 channels (because the STM32 has 4 built in ADCs).
3. Switch off the heating current switch and cut off the heating current.

## Cooling Phase

With these settings done the heating current through the device is cut really fast (~1-2µs) and all the inductive energy is dissipated in the Freewheeling network in parallel to the JUT (on the uTTA power PCB). While the current is freewheeling, the microcontroller is continuously sampling at 2MS/s. After 250 samples the ADC halves its sampling rate to 1MS/s, and after another 250Samples to 500kS/s. This process of taking 250samples and reducing the sample rate is done until the minimum sample rate of ~15.26 Samples/s is reached. From there the sampling continues until the preset measurement time is reached. As the correct timing is extremely crucial to the whole process the sampling is controlled by an internal timer which is set to these sampling rates. The change of sampling rates is performed by the timers’ preload registers which are automatically reloaded as soon as 250 samples were generated.
