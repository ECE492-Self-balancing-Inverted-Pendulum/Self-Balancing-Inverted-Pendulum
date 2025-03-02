import RPi.GPIO as GPIO
import time
import threading

# Motor Driver Pins (using BCM numbering)
MOTOR_IN1 = 13  # PWM control pin
MOTOR_IN2 = 19  # Direction control pin (set LOW for forward rotation)

# Encoder Pins
ENCODER_A = 17  # Encoder channel A
ENCODER_B = 27  # Encoder channel B
CPR = 1024      # Counts per Revolution for the encoder

# PWM and Control Parameters
PWM_FREQ = 1000         # 1 kHz PWM frequency
MIN_PWM = 31.4          # Minimum PWM to overcome motor stiction (motor starts moving at 31.4%)
MAX_PWM = 100           # Maximum PWM value
PWM_STEP = 3            # Maximum allowed PWM change per control cycle (for soft ramp)

# PID Controller Tuning Parameters
Kp = 1.5    # Proportional gain (lowered to reduce oscillations)
Ki = 0.3    # Integral gain (reduced to prevent overshooting)
Kd = 0.8    # Derivative gain (increased to improve damping)
DT = 0.1    # Time step (in seconds) for the control loop

# Global Variables
pulse_count = 0
target_rpm = None
current_rpm = 0
pwm_value = MIN_PWM  # Start at minimum PWM

# PID internal variables
prev_error = 0
integral = 0

# Debug variables for structured logging
debug_error = 0
debug_P = 0
debug_I = 0
debug_D = 0

# Callback function to count encoder pulses
def encoder_callback(channel):
    global pulse_count
    pulse_count += 1

# Function to calculate RPM based on encoder pulses
def calculate_rpm():
    global pulse_count, current_rpm
    while True:
        count = pulse_count
        pulse_count = 0
        # RPM calculation: (counts per second * 60) / CPR
        current_rpm = (count * 60) / CPR
        time.sleep(1)

# PID control loop to adjust PWM dynamically
def control_motor():
    global pwm_value, target_rpm, current_rpm, prev_error, integral
    global debug_error, debug_P, debug_I, debug_D

    while True:
        if target_rpm is None:
            time.sleep(DT)
            continue

        # Compute error between target and measured RPM
        error = target_rpm - current_rpm

        # PID calculations:
        P_term = Kp * error
        integral += error * DT
        I_term = Ki * integral
        derivative = (error - prev_error) / DT
        D_term = Kd * derivative

        # Store PID components for debugging
        debug_error = error
        debug_P = P_term
        debug_I = I_term
        debug_D = D_term

        # PID output before clamping
        pid_output = P_term + I_term + D_term

        # Ensure the output is above the dead zone when a positive RPM is targeted
        if target_rpm > 0:
            pid_output = max(pid_output, MIN_PWM)

        # Clamp the desired PWM within allowed limits
        desired_pwm = max(MIN_PWM, min(MAX_PWM, pid_output))

        # Implement a soft start/gradual change by limiting the PWM step change
        delta = desired_pwm - pwm_value
        if abs(delta) > PWM_STEP:
            pwm_value += PWM_STEP if delta > 0 else -PWM_STEP
        else:
            pwm_value = desired_pwm

        # Apply the new PWM value to the motor
        pwm.ChangeDutyCycle(pwm_value)

        # Update previous error for the next iteration
        prev_error = error

        time.sleep(DT)

# Thread to print structured debugging information every second
def debug_info():
    global target_rpm, current_rpm, pwm_value, debug_error, debug_P, debug_I, debug_D
    # Wait until a target RPM is set
    while target_rpm is None:
        time.sleep(0.5)
    while True:
        print(f"[DEBUG] Target RPM: {target_rpm:.2f}, Current RPM: {current_rpm:.2f}, PWM: {pwm_value:.2f}, "
              f"Error: {debug_error:.2f}, P: {debug_P:.2f}, I: {debug_I:.2f}, D: {debug_D:.2f}")
        time.sleep(1)

def main():
    print("Motor Speed Control Started. Enter target RPM:")
    while True:
        user_input = input("Enter desired RPM (or 'q' to quit): ").strip()
        if user_input.lower() == "q":
            break
        try:
            global target_rpm
            target_rpm = float(user_input)
            print(f"✅ Target RPM set to {target_rpm}")
        except ValueError:
            print("❌ Invalid input. Please enter a valid number.")

# Main program execution
if __name__ == '__main__':
    try:
        # GPIO Setup
        GPIO.setmode(GPIO.BCM)

        # Setup motor control pins
        GPIO.setup(MOTOR_IN1, GPIO.OUT)
        GPIO.setup(MOTOR_IN2, GPIO.OUT)

        # Setup encoder pins with pull-ups
        GPIO.setup(ENCODER_A, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(ENCODER_B, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        # Attach the encoder callback to count pulses on rising edge
        GPIO.add_event_detect(ENCODER_A, GPIO.RISING, callback=encoder_callback)

        # Setup PWM on the motor control pin
        pwm = GPIO.PWM(MOTOR_IN1, PWM_FREQ)
        pwm.start(MIN_PWM)

        # Set fixed motor direction (forward)
        GPIO.output(MOTOR_IN2, GPIO.LOW)

        # Start background threads for RPM measurement, PID control, and debugging
        rpm_thread = threading.Thread(target=calculate_rpm, daemon=True)
        rpm_thread.start()

        pid_thread = threading.Thread(target=control_motor, daemon=True)
        pid_thread.start()

        debug_thread = threading.Thread(target=debug_info, daemon=True)
        debug_thread.start()

        main()

    except KeyboardInterrupt:
        print("\nStopping script...")

    finally:
        pwm.stop()
        GPIO.cleanup()
