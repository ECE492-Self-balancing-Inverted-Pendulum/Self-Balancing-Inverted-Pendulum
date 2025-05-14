# Self-Balancing Inverted Pendulum Robot

This repository contains the complete software stack for a self-balancing inverted pendulum robot project of ECE492: Computer Design Project. The code includes control algorithms, sensor integration, and hardware abstraction layers. The system operates on an embedded platform (Raspberry Pi Zero 2 W) and uses sensor fusion and closed-loop PID control to achieve real-time balancing.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [System Architecture](#system-architecture)
- [Hardware Requirements](#hardware-requirements)
- [Software Requirements](#software-requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Control Theory](#control-theory)
- [Directory Structure](#directory-structure)
- [License](#license)
- [Acknowledgments](#acknowledgments)

---

## Overview

The self-balancing robot functions as a dynamic inverted pendulum system. It uses an onboard microcontroller, an inertial measurement unit (IMU), and DC motors to maintain its upright orientation. This repository provides the source code responsible for processing sensor data, computing control signals, and commanding the actuators.

---

## Features

- Real-time PID control loop for balance
- Sensor fusion via Madgwick filtering
- Support for I2C communication protocols
- Web-based data logging and optional serial plotting support 
- Configurable control parameters via web interface or setting files

---

## System Architecture

```

+-----------------+            +---------------------------+         +-----------------+
|  IMU (ICM-20948)  | ---->   | Sensor Filter(Madgwick)   | ---->   | PID Controller  |
+-----------------+            +---------------------------+         +-----------------+
|
v
+---------------------+
| Motor Driver (PWM)  |
+---------------------+

````

- The IMU supplies pitch angle and angular velocity data.
- The Sensor filter utilizes madgwick filter to revent noise and ensure stable operations.
- The PID controller calculates corrective torque based on the tilt.
- Motor drivers actuate the wheels to maintain balance.

---

## Hardware Requirements

- Microcontroller (Raspberry Pi Zero 2W)
- Inertial Measurement Unit (ICM-20948)
- Motor Driver (DRV8871)
- DC motors with gear reduction (with or without encoders)
- Chassis with two wheels
- Power source (e.g., LiPo battery or regulated power supply)

---

## Software Requirements

- Pi OS
- Python environment


---

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/ECE492-Self-balancing-Inverted-Pendulum/Self-Balancing-Inverted-Pendulum.git
   ```

2. Open the project in your development environment (Onboard OS)

3. Run PID_Control/main.py

---

## Usage

1. Place the robot upright on a flat surface and power it on.
2. Monitor the serial console to confirm initialization.
3. If PID tuning via serial interface is enabled, adjust the parameters accordingly.
4. Observe the balancing behavior and make additional tuning adjustments if necessary.

---

## Control Theory

The system is based on a classical Proportional-Integral-Derivative (PID) control model. The controller calculates an error term based on the deviation of the robot’s current tilt angle from the vertical and applies corrective action via the motors.

$$
u(t) = K_p \cdot e(t) + K_i \cdot \int e(t)\,dt + K_d \cdot \frac{de(t)}{dt}
$$

Where:

* $u(t)$ is the control signal (PWM duty cycle percentage),
* $e(t)$ is the pitch error,
* $K_p, K_i, K_d$ are the proportional, integral, and derivative gains, respectively.

A Madgwick is used to obtain an accurate estimate of the pitch angle from noisy accelerometer and gyroscope readings.

---

## Directory Structure

```
Self-Balancing-Inverted-Pendulum/
├── IMU/                    # Inertial Measurement Unit interfacing and sensor fusion
├── PID_Control/            # PID control algorithm implementations
├── SIPERlib.egg-info/      # Metadata for the SIPERlib Python package
├── build/
│   └── lib/
│       └── SIPERlib/       # Compiled library files
├── dist/                   # Distribution packages for deployment
├── lib.egg-info/           # Additional package metadata
├── main/                   # Main application code and entry points
├── motor_driver/           # Motor driver interfaces and control logic
├── motor_simulation/       # Simulation tools for motor behavior
├── unorganized/            # Miscellaneous or yet-to-be-organized files
├── .gitignore              # Specifies files to ignore in version control
├── .motorCntr_encoder.py.swp  # Temporary swap file (likely from an editor)
├── README                  # Project overview and documentation
├── requirements.txt        # List of Python dependencies
└── setup.py                # Setup script for building and installing the package

```

## License

This project is licensed under the MIT License. See the [LICENSE](LISCENSE.txt) file for more details.

---

## Acknowledgments

This project is inspired by educational and open-source efforts in the fields of robotics, embedded systems, and control theory. Special thanks to the Steven Knudsen, Steve Drake and Michael Lipsett for their guidance and instruction.


