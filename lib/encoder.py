import RPi.GPIO as GPIO
import time

class Encoder:
    def __init__(self, pin_a, pin_b, cpr=1024):
        self.pin_a = pin_a
        self.pin_b = pin_b
        self.cpr = cpr
        self.pulse_count = 0

        # Setup GPIO
        GPIO.setup(self.pin_a, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.pin_b, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        # Attach interrupt for encoder pulse counting
        GPIO.add_event_detect(self.pin_a, GPIO.RISING, callback=self._encoder_callback)

    def _encoder_callback(self, channel):
        self.pulse_count += 1  # Increment pulse count on each rising edge

    def measure_rpm(self, duration=1):
        self.pulse_count = 0  # Reset counter
        time.sleep(duration)  # Measure for 'duration' seconds
        rpm = (self.pulse_count * 60) / self.cpr  # Convert to RPM
        return rpm

