import RPi.GPIO as GPIO
import time

# Encoder Pins
ENCODER_A_PIN = 17  # Channel A
ENCODER_B_PIN = 27  # Channel B
INDEX_PIN = 22       # Index signal

# Variables
pulse_count = 0
measurement_started = False
first_index_detected = False

# Callback function to count pulses
def encoder_callback(channel):
    global pulse_count, measurement_started
    if measurement_started:
        pulse_count += 1

# Callback function to detect index pulse
def index_callback(channel):
    global first_index_detected, measurement_started, pulse_count
    
    if not first_index_detected:
        # First index detected, ignore it and reset flag
        first_index_detected = True
        print("First Index detected, waiting for it to reset...")
        return  # Ignore the first detection

    if not measurement_started:
        # Start counting when the index resets to LOW
        while GPIO.input(INDEX_PIN) == 1:  
            time.sleep(0.001)  # Wait until Index goes LOW

        print("Index reset. Starting pulse count...")
        pulse_count = 0  # Reset pulse count
        measurement_started = True
    else:
        # Second index detected, print CPR and reset for next rotation
        print(f"Full rotation detected! CPR = {pulse_count}")
        pulse_count = 0  # Reset pulse count
        measurement_started = False
        first_index_detected = False  # Allow continuous measurement

# GPIO setup
GPIO.setmode(GPIO.BCM)
GPIO.setup(ENCODER_A_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(ENCODER_B_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(INDEX_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Attach interrupts
GPIO.add_event_detect(ENCODER_A_PIN, GPIO.BOTH, callback=encoder_callback)
GPIO.add_event_detect(INDEX_PIN, GPIO.RISING, callback=index_callback)

try:
    print("Rotate the wheel. The script will measure CPR for each full rotation.")
    while True:
        time.sleep(0.1)  # Keep script running

except KeyboardInterrupt:
    print("\nStopping script...")
    GPIO.cleanup()

