import RPi.GPIO as GPIO
import time
import csv

# Motor Driver Pins
MOTOR_IN1 = 13  # PWM control pin
MOTOR_IN2 = 19  # Direction pin (set LOW for forward rotation)

# Encoder Pins
ENCODER_A = 17  # Channel A
ENCODER_B = 27  # Channel B
CPR = 1024  # Confirmed Counts Per Revolution (CPR)

# PWM Frequency
PWM_FREQ = 1000  # 1 kHz

# Variables
pulse_count = 0
duty_cycle_values = range(0, 100, 5)  # 0% to 100% PWM in steps of 10%
data = []  # Store results

# Callback function to count encoder pulses
def encoder_callback(channel):
    global pulse_count
    pulse_count += 1  # Count pulses only on rising edge of Channel A

# GPIO setup
GPIO.setmode(GPIO.BCM)

# Motor Control Setup
GPIO.setup(MOTOR_IN1, GPIO.OUT)  # Set as PWM output
GPIO.setup(MOTOR_IN2, GPIO.OUT)  # Set as digital output

# Encoder Setup
GPIO.setup(ENCODER_A, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(ENCODER_B, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Attach interrupt for encoder pulse counting (rising edge only)
GPIO.add_event_detect(ENCODER_A, GPIO.RISING, callback=encoder_callback)

# Setup PWM on MOTOR_IN1
pwm = GPIO.PWM(MOTOR_IN1, PWM_FREQ)  # Create PWM object
pwm.start(0)  # Start PWM at 0% duty cycle

# Set fixed direction (forward)
GPIO.output(MOTOR_IN2, GPIO.LOW)

try:
    print("Measuring PWM vs RPM...")

    for duty_cycle in duty_cycle_values:
        pwm.ChangeDutyCycle(duty_cycle)  # Set PWM duty cycle
        time.sleep(2)  # Allow time for motor to stabilize

        pulse_count = 0  # Reset pulse counter
        time.sleep(1)  # Measure pulses for 1 second
        rpm = (pulse_count * 60) / CPR  # Convert to RPM

        print(f"PWM: {duty_cycle}% -> RPM: {rpm:.2f}")
        data.append([duty_cycle, rpm])  # Store data

    # Save data to CSV file
    with open("pwm_vs_rpm.csv", "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["PWM (%)", "RPM"])
        writer.writerows(data)

    print("\nData saved to pwm_vs_rpm.csv.")
    
finally:
    print("\nStopping script...")
    pwm.stop()
    GPIO.cleanup()
