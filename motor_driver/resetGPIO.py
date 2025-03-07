import RPi.GPIO as GPIO
import time

def reset_gpio():
    """
    Fully resets all GPIO pins to prevent reinitialization issues.
    """
    print("[INFO] Resetting GPIO...")

    # Disable warnings to avoid "channel already in use" messages
    GPIO.setwarnings(False)

    # Cleanup any existing GPIO setup
    GPIO.cleanup()

    # Short delay to ensure cleanup is applied
    time.sleep(0.5)

    print("[INFO] GPIO Reset Complete.")

if __name__ == "__main__":
    reset_gpio()

