from machine import Pin, PWM
from time import sleep

# Motor driver pins (adjust according to your wiring)
IN1 = Pin(12, Pin.OUT)
IN2 = Pin(18, Pin.OUT)
ENA = PWM(Pin(12))  # Enable pin connected to PWM-capable GPIO

# Set the PWM frequency and start with 0 duty cycle
ENA.freq(1000)
ENA.duty_u16(0)

# Function to move motor forward
def forward(speed):
    IN1.high()
    IN2.low()
    ENA.duty_u16(int(speed * 65535))  # Speed: 0.0 to 1.0

# Function to move motor backward
def backward(speed):
    IN1.low()
    IN2.high()
    ENA.duty_u16(int(speed * 65535))

# Function to stop the motor
def stop():
    IN1.low()
    IN2.low()
    ENA.duty_u16(0)

# Test the motor
try:
    while True:
        print("Moving Forward")
        forward(0.7)  # 70% speed
        sleep(2)
        
        print("Stopping")
        stop()
        sleep(1)
        
        print("Moving Backward")
        backward(0.5)  # 50% speed
        sleep(2)
        
        print("Stopping")
        stop()
        sleep(1)
        
        print("Moving Forward to the MAX")
        forward(1)  # 100% speed
        sleep(2)
        
        print("Stopping")
        stop()
        sleep(1)
        
        print("Moving Backward to the MAX")
        backward(1)  # 100% speed
        sleep(2)

except KeyboardInterrupt:
    print("Program stopped")
    stop()


