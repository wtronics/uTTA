# uTTA — The Micro ($\mu$) Thermal Transient Analyzer

## What's this TTA stuff anyhow?

Thermal Transient Analysis (TTA) is an advanced technique used to determine the thermal impedance model of a cooling path by measuring its thermal step response. This method is rigorously specified in the **JESD 51-14** standard and is brilliantly summarized in the following tutorials:
* [Transient thermal measurements and thermal equivalent circuit models](https://www.infineon.com/dgdl/Infineon-Thermal_equivalent_circuit_models-ApplicationNotes-v01_02-EN.pdf?fileId=db3a30431a5c32f2011aa65358394dd2) *(Highly recommended!)*
* [Structure function based evaluation of the thermal behavior of an LED](https://repository.tugraz.at/publications/1bz3b-q3w35) *(Definitely worth to read)*

Ideally, after completing a measurement, you should be able to transform the raw captured data into a thermal impedance ($Z_{th}$) curve—a staple graph found in almost every power semiconductor datasheet. In a nutshell, a $Z_{th}$ curve allows engineers to read the specific thermal resistance encountered by a device when a rectangular power pulse of a given duration $x$ is applied. By combining this thermal resistance with the dissipated power, you can calculate the exact junction temperature of the semiconductor at the end of that pulse. 

However, this math only holds true as long as the power pulse is brief enough not to hit the physical thermal boundaries of the semiconductor package itself. Once the heat propagates past those boundaries and into the rest of the assembly, you need a dedicated thermal impedance curve tailored to your specific, real-world cooling path. Nexperia published an excellent application note diving deeper into this topic: 
* [Nexperia AN11156](https://assets.nexperia.com/documents/application-note/AN11156.pdf)

Things get significantly more complicated when dealing with non-rectangular power pulses. While an "extended rectangular" approximation works for a rough estimate, it demands a massive amount of manual effort. Furthermore, if your ultimate goal is running a dynamic thermal simulation, static datasheet graphs are practically useless. For simulation purposes, the most elegant approach is to model the thermal cooling path using a network of RC circuits that mimic the system's heating and cooling behavior. Again, Nexperia offers a fantastic guide on how this is done: 
* [Nexperia AN11261](https://assets.nexperia.com/documents/application-note/AN11261.pdf)

But how do you actually extract these RC models for a specific power semiconductor combined with a custom heatsink? This is where the real headache begins. While you might occasionally find thermal models for a MOSFET, they are almost exclusively provided as encrypted SPICE models. Nexperia is one of the few refreshing exceptions, sometimes offering open thermal equivalent RC networks (structured as either Foster or Cauer models). But when it comes to the heatsink, manufacturers typically provide nothing more than a single, static thermal resistance value.

---

## How to perform these measurements?
### The Proper (and Expensive) Way
Capturing high-fidelity thermal transient measurements requires highly specialized hardware. The industry standard system is called **T3Ster**, originally engineered by MicReD (a Hungarian company later acquired by Siemens). 

Unsurprisingly, industrial equipment like this costs an absolute fortune—well into the high 5-to-6-figure Euro range. Because such professional tools are completely inaccessible for hobbyist or educational budgets, I set out to design and build my own miniature alternative.

### My own little Thermal Transient Analyzer (uTTA)
uTTA began as a passion project during the first COVID-19 lockdown. At the time, I was experimenting heavily with various power electronics (mostly MOSFET-based power switches and electronic loads) and kept running into the exact same wall: *How long can I dissipate a specific amount of surge power in this MOSFET before it reaches its critical destructive temperature?*

While several theoretical methods exist to solve this, every single one of them requires you to know the exact thermal impedance curve of your unique mechanical setup.

#### Target Picture
The following checklist outlines the core objectives of this project and what has been successfully accomplished so far:
* [x] **Measurement Hardware:** Design a hardware platform capable of performing single-channel thermal impedance measurements while simultaneously monitoring at least 2 additional channels for future thermal coupling analysis.
* [x] **Postprocessing Software:** Build a software toolkit to process raw measurement data and extract clean thermal impedance ($Z_{th}$) curves.
* [x] **Thermal Coupling:** Add software/hardware support to measure thermal coupling between adjacent semiconductors.
* [x] **Self-Calibration:** Implement software utilities to calibrate the internal measurement hardware.
* [ ] **Time Constant Spectra:** Implement the ability to calculate the time constant spectrum of the $Z_{th}$ curve via the NID (Network Identification by Deconvolution) method (utilizing either classical FFT deconvolution or a Bayesian approach).
* [ ] **RC Model Extraction:** Automatically extract equivalent RC thermal networks directly from the calculated time constant spectrum.
* [x] **Junction Calibration:** Develop software and hardware tools to calibrate the temperature coefficient of the junction under test.
* [ ] **Hardware Simulator:** Build a dedicated hardware simulator capable of generating highly predictable and repeatable cooling curves to rigorously validate all subsequent software processing steps.

#### Design Requirements
The device must adhere to the following constraints:
* **User-Friendly:** It should be straightforward and intuitive to operate.
* **Cost-Effective:** Extremely cheap and easy to replicate. Target budget: **€150** covering all components and the PCB.
* **Highly Available:** Rely exclusively on off-the-shelf components; absolutely no hard-to-find or "unobtanium" parts.
* **High-Current Handling:** Integrate an onboard heating current switch rated for up to 15A DC which could be upgraded to even higher heating currents.
* **Auxiliary Sensing:** Include a few Type-K thermocouple interfaces for low-speed ambient/heatsink monitoring (< 5 Samples/s).
* **Multi-Junction Tracking:** Capable of measuring the primary Junction Under Test (JUT) alongside 2 secondary monitoring junctions to evaluate thermal coupling.
* **Dynamic Range Optimization:** Provide software-selectable gain settings for the JUT monitor to maximize ADC resolution throughout the transient event.
* **High-Speed Sampling Speed:** Deliver an ultra-fast sampling rate of at least 1MS/s immediately following the deactivation of the heating current to capture the critical early transient behavior.
* **Intelligent Data Reduction:** Automatically taper down the sampling rate as the transient slows down, preventing the accumulation of massive, redundant data logs.
* **Onboard Storage:** Buffer all high-speed data directly to built-in local memory.
* **PC Control:** Managed entirely via a clean, accessible PC graphical user interface (GUI).

---

# The Implementation

## µTTA Hardware
This is the current physical state of the µTTA hardware. The architecture utilizes a compact 3-layer PCB stack enclosed in a custom 3D-printed housing. The design files for the mechanical housing are available under `010_Hardware/060_Mechanics`.

![uTTA_Device_Setup_Annotated](https://github.com/user-attachments/assets/7c182419-f98b-485b-b2a3-c33c398a1492)

## The Final Test Setup (Simplified)
Below is an overview of the active test setup. The JUT assembly is positioned right next to the power supply. 

> **Note on Environment:** In a professional testing environment, the JUT assembly must be enclosed in a "still air chamber" to isolate the measurement from volatile ambient drafts. Ideally, the device would be mounted onto a temperature-controlled cold plate, but that represents an unnecessary layer of complexity for the scope of this hobby project.

![Simple_Test_Setup](https://github.com/user-attachments/assets/ae0f6380-08d0-41af-bd2d-36de6dc38122)

The system is composed of the following core blocks:

### The Heating Power Supply
This unit drives the raw heating current through the Junction Under Test (JUT). While I happen to use a massive 40A bench supply in my lab, any standard power supply featuring an adjustable current limit up to 10A is perfectly adequate for most scenarios. 

The exact current required depends heavily on the specific junction properties and the thermal resistance of the cooling assembly under evaluation. If you are targeting a high-power device with ultra-low thermal resistance (e.g., < 10 K/W), a meatier power supply becomes necessary to force a measurable temperature delta. The supply voltage itself is uncritical; in my configurations, I typically set it to roughly 3V, which provides plenty of headroom to comfortably drive the required current.

### The Junction Under Test
*(To be continued...)*

---

## The JUT Setup

Lacking access to a formal industrial application board I can show in public, I assembled a custom test fixture that closely mimics real-world conditions. The setup consists of three spare MOSFETs bolted to a shared aluminum heatsink. 
The transistors are electrically isolated from the heatsink using standard mica ("glimmer") washers and silicone thermal pads. However, to establish a shared return path for the sense current across all monitored devices, the isolating washers on the mounting screws were intentionally omitted to bridge the drains of all three MOSFETs together. The Gate and Source pins of each individual MOSFET are shorted to prevent spurious turn-on events triggered by static charges. 
Furthermore, each MOSFET is routed through a dedicated coaxial sense cable to accurately monitor the forward voltage drop of the internal body diodes and supply the delicate measurement current. The primary heated junction is also hooked up to heavy-gauge wires to carry the high heating current. These low-inductance lines are custom-made by braiding high-frequency (HF) litz wire. To minimize the overall loop area and shield against inductive voltage spikes, the positive and negative current paths are tightly bundled inside a braided insulating sleeve.

![JUT_on_Heatsink](https://github.com/user-attachments/assets/10768b4d-3334-4fc3-a089-28a2de61916c)

# ToDo
- [x] Build calibration GUI for uTTA hardware.
- [x] Build calibration GUI for DUT scaling factors.
- [x] Document ST Nucleo-Board jumper configurations.
- [ ] Get the mathematical deconvolution algorithm fully operational.
- [ ] Implement automatic RC-model calculation from the time constant spectrum.
- [ ] Develop a modern, native standalone GUI (moving away from LabVIEW).
- [ ] Overhaul and expand the general documentation.


# Possible Improvements for Future Designs
- [ ] Implement finer gain steps for low-level diode voltage measurements.
- [x] Integrate software-controlled offset adjustment via an onboard DAC.
- [x] Integrate software-adjustable measurement current sources (e.g., DAC-controlled Enhanced Howland Current Sources).
- [ ] Migrate away from the ST Nucleo breakout ecosystem in favor of a fully custom, integrated PCB design. *(Benefits: Eliminates bulky stack-up connectors, drastically improves high-speed signal integrity, allows a highly stable dedicated ADC voltage reference, and enables a native onboard USB interface bypassing the ST-Link debugger).*

## Design Choices

Let's be candid: this system is far from a flawless commercial product. As stated at the beginning, this started as a quick-and-dirty quarantine project during the COVID-19 pandemic. I never anticipated that I would still be actively evolving it over 6 years later. The subject matter completely hooked me, though personal commitments have limited the amount of focused time I can dedicate to it. Because both the hardware and software architectures have undergone iterative overhauls, some design choices might appear slightly unorthodox to an outside observer. Here is the underlying engineering rationale:

* **Why store measurement data in local flash memory instead of streaming it directly to a PC over a serial interface?**
  * Our serial connection maxes out at 250 kBaud, which is fundamentally incapable of sustaining the throughput required during the initial 1 MS/s ultra-fast sampling window. Additionally, the microcontroller lacks the RAM capacity required to buffer the millions of high-speed points simultaneously before a delayed dump. Therefore, high-speed hardware-level buffering to external non-volatile storage was mandatory. While I initially used a micro SD card running FATfs, the aggressive write cycles quickly destroyed the cards. Upgrading to a robust NOR Flash chip running **littleFS** completely solved this reliability bottleneck.

* **Why is there only one switchable amplifier? Shouldn't every tracking channel have its own dynamic gain stage?**
  * The switchable programmable gain amplifier (PGA) is intentionally reserved for the primary heated channel. When the massive heating current passes through the JUT, its forward voltage is substantially larger due to the internal resistance. The amplifier must dynamically drop its gain down during this phase to prevent clipping and keep the signal within the measurable ADC window. 
  * The secondary channels, by contrast, are strictly passive—they monitor adjacent unheated diodes utilizing a constant, low-level measurement current where no severe voltage swings occur. A fixed gain stage is perfectly sufficient to map standard silicon diodes or MOSFET body diodes across these monitoring channels.

* **Why did you build the original GUI in LabVIEW?**
  * Frankly, because I use it daily in my day job as a self-proclaimed "lazy" senior hardware developer! 😉 In industrial prototyping, test software needs to be deployed rapidly, and that is precisely where LabVIEW excels. 
  * I am well aware that LabVIEW is quite polarizing in the developer community, but for whipping together a functional, interactive GUI without getting bogged down in TKinter or basic UI positioning math, it remains an incredibly fast tool.
  * **Update (July 1, 2026):** The complete postprocessing toolchain has now been successfully migrated to a modern Python ecosystem utilizing `TTKbootstrap`. Consequently, I am officially working on sunsetting the legacy LabVIEW GUI in upcoming releases. The foundational groundwork was recently completed following the development of our native SCPI driver for the uTTA hardware.

* **Why power the gate driver of the high-current heating switch with an external battery instead of a standard bench supply?**
  * In the early prototyping phases, I did use a secondary isolated bench supply to power the gate drive circuitry. However, I found myself locked in an endless, frustrating battle with nasty common-mode noise issues during high-current switching events. Swapping that power rail over to a completely floating 9V/12V battery completely severed the noise path and instantly wiped out all common-mode artifacts.

---

# A Note on AI

Given how pervasive AI has become in modern software development, I wanted to include a brief, transparent disclosure regarding its role in this repository. This project leverages generative AI to accelerate development velocities and explore alternative conceptual approaches. 

To be clear: the core firmware running on the microcontroller is entirely handwritten from scratch. On the host PC side, things are a bit more collaborative. I heavily utilize AI to spin up structural boilerplate, generate templates, and prototype abstract UI concepts. For instance, the clean HTML layout used to compile the final measurement reports was largely authored by AI, as LLMs are remarkably proficient at building attractive front-end layouts. 

That being said, every single line of code or structural layout spat out by an AI is meticulously peer-reviewed by a human before merging. AI tools are notoriously confident when generating bugs; for example, LLMs absolutely love using deprecated syntax or obsolete methods from older versions of `tkinter` and `TTKbootstrap`. Treat it as a highly capable but slightly reckless assistant!

P.S.: This reame was also redacted by AI :). 