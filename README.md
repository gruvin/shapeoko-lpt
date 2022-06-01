# Shapeoko UCCNC Upgrade

### Replacing [Shapeoko Pro XL](https://shop.carbide3d.com/collections/machines/products/shapeoko-pro-cnc-router?variant=33007028797501) basic stepper drivers and ditching GRBL in favour of advanced [UCCNC](https://cncdrive.com/UCCNC.html) Controller, using [UC100](https://cncdrive.com/UC100.html) USB interface to plug into this board.

## Why?

Mostly because I really like being able to pause, rewind, start, stop and see toolpaths in realtime. Call me old fashion. 

As a bonus, we get waaaaaay smoother, faster and generally more reliable stepper motors, using "proper" drivers.

## Features

Firstly, I didn't want to cut any wires ...

- Uses original Carbide3D Shapeoko power brick 24VDC @ 5A. (MOSFET switch and onboard 5V supply should handle double that V/A no problem.)
- Uses all original Shapeoko connectors for Power Switch (with blue LED), End Stops, BitSetter & BitZero. (An adapter board for the stepper motors is coming. The latter will be one each for the motor outputs on the stepper drivers.)

... etcetera ...
- Connects to your choice of "decent" stepper drivers

- Provides 24VDC/5A Charge Pump Switched power for drivers. Each of X/Y/Z ports has +5V/STEP/DIR/EN outputs (active low and Y1/Y2 are wired in parrallel or series. Your chpoice.)

- Built-in safety "charge pump" prevents 24VDC coming live until UCCNC is up and ready on the PC (can be bypassed with jumper.)

- VFD Spindle control with 0-10V speed control

- External 3 relay connector (4 if no charge pump). Relay 1 of 4 operates from EN (stepper enable). Relay 2 and 3 are connected to LPT P8 and P9 (Flood/Mist/Vacuum/Air.)

- Onboard 5VDC 1A supply.

- Input for **!! EMMERGENCY STOP !!** (normally closed switch.) Currently, the signal just goes to LPT P1, for your controller software (USCNC/Mach3) to deal with. Can use for that or Feed Hold if preferred.

## Status
### 2022-06-02 

First batch of assembled prototype PCBs were a bust due to both errors and having been obsoleted by lots of design changes since ordering them.

Trying to get a full week without making any chages before ordering a set of V2.0.



### KiCAD sneak peek, very much a work in progress ...

<img width="1024" alt="Top_V2.0_WIP.png" src="https://github.com/gruvin/shapeoko-lpt/raw/master/images/Top_V2.0_WIP.png">

<img width="1024" alt="Bottom_V2.0_WIP.png" src="https://github.com/gruvin/shapeoko-lpt/raw/master/images/Bottom_V2.0_WIP.png">
