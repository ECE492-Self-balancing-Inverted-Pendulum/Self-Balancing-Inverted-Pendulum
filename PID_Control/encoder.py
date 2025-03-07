import RPi.GPIO as GPIO
import time

class Encoder:
    def __init__(self, pin_a, pin_b, cpr=1024):
        """
        Initializes the encoder.
        
        :param pin_a: GPIO pin for encoder channel A
        :param pin_b: GPIO pin for encoder channel B
        :param cpr: Counts per revolution (default: 1024)
        """
        self.pin_a = pin_a
        self.pin_b = pin_b
        self.cpr = cpr
        self.pulse_count = 0

        # Setup GPIO
        GPIO.setwarnings(False)  # Prevent "channel already in use" warnings
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin_a, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.pin_b, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        # Attach interrupt for encoder pulse counting
        GPIO.remove_event_detect(self.pin_a)
        GPIO.add_event_detect(self.pin_a, GPIO.RISING, callback=self._encoder_callback)

    def _encoder_callback(self, channel):
        """
        Callback function to count encoder pulses.
        """
        self.pulse_count += 1

    def measure_rpm(self, duration=1):
        """
        Measures the RPM of the motor.

        :param duration: Measurement time in seconds (default: 1s)
        :return: Calculated RPM
        """
        self.pulse_count = 0  # Reset counter
        time.sleep(duration)  # Measure for 'duration' seconds
        rpm = (self.pulse_count * 60) / self.cpr  # Convert to RPM
        return rpm

    def cleanup(self):
        """
        Cleans up GPIO to prevent resource conflicts.
        """
        GPIO.remove_event_detect(self.pin_a)  # Remove interrupt detection
        GPIO.cleanup([self.pin_a, self.pin_b])  # Cleanup only the used GPIOs
        print("[INFO] Encoder GPIO cleaned up.")

# Example usage
if __name__ == "__main__":
    encoder = Encoder(pin_a=17, pin_b=27)

    try:
        while True:
            rpm = encoder.measure_rpm()
            print(f"RPM: {rpm:.2f}")
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping encoder.")
    finally:
        encoder.cleanup()

