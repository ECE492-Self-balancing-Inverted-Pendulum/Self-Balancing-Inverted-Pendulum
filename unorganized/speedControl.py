import RPi.GPIO as GPIO
import time
import threading

# Motor Driver Pins (using BCM numbering)
MOTOR_IN1 = 13   # PWM control pin
MOTOR_IN2 = 19   # Direction control pin (set LOW for forward rotation)

# Encoder Pins
ENCODER_A = 17   # Encoder channel A
ENCODER_B = 27   # Encoder channel B
CPR = 1024       # Counts per Revolution for the encoder

# PWM and Control Parameters
PWM_FREQ = 1000         # 1 kHz PWM frequency
MIN_PWM = 0             # Operating from 0%
MAX_PWM = 100           # Up to 100% PWM
PWM_STEP = 3            # Maximum allowed change per control cycle

# Motor Characteristic
MOTOR_MAX_RPM = 650     # Expected RPM at 100% PWM

# PID Controller Tuning Parameters (revised)
Kp = 0.3                # Proportional gain (reduced)
Ki = 0.02               # Integral gain (reduced)
Kd = 0.005              # Derivative gain (reduced)
DT = 0.1                # Control loop time step (seconds)
I_MAX = 100             # Integral wind-up limit (reduced)

# Global Variables
pulse_count = 0
target_rpm = None
current_rpm = 0
pwm_value = MIN_PWM     # Start at 0% PWM

# PID internal variables
prev_error = 0
integral = 0

# Debug variables for detailed logging
debug_error = 0
debug_P = 0
debug_I = 0
debug_D = 0
debug_pid_output = 0
debug_feed_forward = 0
debug_desired_pwm = 0
debug_delta = 0
debug_integral = 0
debug_derivative = 0
debug_prev_error = 0

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
        # RPM = (pulses in DT sec * 60) / CPR
        current_rpm = (count / DT) * 60 / CPR
        time.sleep(DT)

# PID control loop with feed-forward and comprehensive debug logging
def control_motor():
    global pwm_value, target_rpm, current_rpm, prev_error, integral
    global debug_error, debug_P, debug_I, debug_D, debug_pid_output, debug_feed_forward
    global debug_desired_pwm, debug_delta, debug_integral, debug_derivative, debug_prev_error

    while True:
        if target_rpm is None:
            time.sleep(DT)
            continue

        # Calculate feed-forward term based on open-loop mapping:
        # feed_forward = (target_rpm / MOTOR_MAX_RPM) * MAX_PWM
        feed_forward = (target_rpm / MOTOR_MAX_RPM) * MAX_PWM
        debug_feed_forward = feed_forward

        # Compute error (target RPM - current RPM)
        error = target_rpm - current_rpm

        # PID calculations
        P_term = Kp * error
        integral += error * DT
        if integral > I_MAX:
            integral = I_MAX
        elif integral < -I_MAX:
            integral = -I_MAX
        I_term = Ki * integral
        derivative = (error - prev_error) / DT
        D_term = Kd * derivative

        pid_correction = P_term + I_term + D_term

        # Save debug values
        debug_error = error
        debug_P = P_term
        debug_I = I_term
        debug_D = D_term
        debug_pid_output = pid_correction
        debug_integral = integral
        debug_derivative = derivative
        debug_prev_error = prev_error

        # Total desired PWM = feed-forward + PID correction
        desired_pwm = feed_forward + pid_correction
        desired_pwm = max(MIN_PWM, min(MAX_PWM, desired_pwm))
        debug_desired_pwm = desired_pwm

        # Soft ramping: limit change per update
        delta = desired_pwm - pwm_value
        debug_delta = delta
        if abs(delta) > PWM_STEP:
            pwm_value += PWM_STEP if delta > 0 else -PWM_STEP
        else:
            pwm_value = desired_pwm

        pwm.ChangeDutyCycle(pwm_value)
        prev_error = error

        time.sleep(DT)

# Debug thread prints comprehensive debug info every second
def debug_info():
    while target_rpm is None:
        time.sleep(0.5)
    while True:
        print("=== DEBUG INFO ===")
        print(f"Target RPM:      {target_rpm:.2f}")
        print(f"Current RPM:     {current_rpm:.2f}")
        print(f"Feed-Forward:    {debug_feed_forward:.2f}")
        print(f"PWM Value:       {pwm_value:.2f}")
        print(f"Error:           {debug_error:.2f}")
        print(f"P Term:          {debug_P:.2f}")
        print(f"I Term:          {debug_I:.2f} (Integral: {debug_integral:.2f})")
        print(f"D Term:          {debug_D:.2f} (Derivative: {debug_derivative:.2f})")
        print(f"PID Correction:  {debug_pid_output:.2f}")
        print(f"Desired PWM:     {debug_desired_pwm:.2f}")
        print(f"Delta Applied:   {debug_delta:.2f}")
        print(f"Previous Error:  {debug_prev_error:.2f}")
        print("===================")
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

if __name__ == '__main__':
    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(MOTOR_IN1, GPIO.OUT)
        GPIO.setup(MOTOR_IN2, GPIO.OUT)
        GPIO.setup(ENCODER_A, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(ENCODER_B, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        GPIO.add_event_detect(ENCODER_A, GPIO.RISING, callback=encoder_callback)

        pwm = GPIO.PWM(MOTOR_IN1, PWM_FREQ)
        pwm.start(pwm_value)
        # Set motor direction (adjust if needed for your wiring)
        GPIO.output(MOTOR_IN2, GPIO.LOW)

        threading.Thread(target=calculate_rpm, daemon=True).start()
        threading.Thread(target=control_motor, daemon=True).start()
        threading.Thread(target=debug_info, daemon=True).start()

        main()

    except KeyboardInterrupt:
        print("\nStopping script...")

    finally:
        pwm.stop()
        GPIO.cleanup()

