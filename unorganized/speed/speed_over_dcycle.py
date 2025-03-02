import RPi.GPIO as GPIO
import time
import math

# Use BCM pin numbering
GPIO.setmode(GPIO.BCM)

# Motor Control Pins (PWM)
IN1 = 13  # Motor direction and PWM speed control
IN2 = 19  # Motor direction and PWM speed control

# Encoder Pins (Quadrature A & B)
ENCODER_A = 17
ENCODER_B = 27

# Motor & Wheel Specifications
V_MOTOR = 6.8  # Motor operating voltage (V)
I_MAX = 2.0    # Max motor current (A)
WHEEL_DIAMETER = 0.11  # Wheel diameter in meters (11 cm)
CPR = 1024  # Encoder Cycles Per Revolution (modify as per encoder)

# Set up GPIOs
GPIO.setup(IN1, GPIO.OUT)
GPIO.setup(IN2, GPIO.OUT)
GPIO.setup(ENCODER_A, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(ENCODER_B, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Set up PWM (1 kHz frequency)
pwm1 = GPIO.PWM(IN1, 1000)
pwm2 = GPIO.PWM(IN2, 1000)
pwm1.start(0)
pwm2.start(0)

# Encoder counter
encoder_pulse_count = 0

# Interrupt callback for encoder counting
def encoder_callback(channel):
    global encoder_pulse_count
    a_state = GPIO.input(ENCODER_A)
    b_state = GPIO.input(ENCODER_B)

    # Determine direction
    if a_state == b_state:
        encoder_pulse_count += 1  # Clockwise
    else:
        encoder_pulse_count -= 1  # Counterclockwise

# Attach interrupt for Encoder A signal
GPIO.add_event_detect(ENCODER_A, GPIO.RISING, callback=encoder_callback)

# Function to calculate RPM
def calculate_rpm():
    global encoder_pulse_count
    pulses = encoder_pulse_count
    encoder_pulse_count = 0  # Reset count after reading
    rpm = (pulses / CPR) * 60  # Convert pulses to RPM
    return rpm

# Function to convert RPM to Speed (m/s)
def rpm_to_speed(rpm, wheel_diameter=WHEEL_DIAMETER):
    radius = wheel_diameter / 2  # Convert diameter to radius
    speed_mps = (2 * math.pi * radius * rpm) / 60  # Speed in meters per second
    return speed_mps

# Function to set motor speed
def set_motor_speed(speed):
    pwm1.ChangeDutyCycle(speed)  # PWM on IN1
    pwm2.ChangeDutyCycle(0)      # IN2 off

# Store results
data = []

try:
    print("Measuring speed vs duty cycle...")

    for duty_cycle in range(0, 101, 5):  # Iterate duty cycle from 0 to 100%
        set_motor_speed(duty_cycle)
        time.sleep(2)  # Allow motor to stabilize

        rpm = calculate_rpm()
        speed_mps = rpm_to_speed(rpm)

        data.append([duty_cycle, rpm, speed_mps])

        print(f"Duty Cycle: {duty_cycle}%, RPM: {rpm}, Speed: {speed_mps:.2f} m/s")

    # Stop motor
    set_motor_speed(0)
    
    # Convert data to a Pandas DataFrame
    # df = pd.DataFrame(data, columns=["Duty Cycle (%)", "RPM", "Speed (m/s)"])
    
    # Export to CSV
    #csv_filename = "speed_vs_duty_cycle.csv"
    #df.to_csv(csv_filename, index=False)
    #print(f"\n✅ Data exported successfully to {csv_filename}")

    # Display table
    #import ace_tools as tools
    #tools.display_dataframe_to_user(name="Speed vs Duty Cycle", dataframe=df)

except KeyboardInterrupt:
    print("Interrupted, stopping motor.")

finally:
    pwm1.stop()
    pwm2.stop()
    GPIO.cleanup()

