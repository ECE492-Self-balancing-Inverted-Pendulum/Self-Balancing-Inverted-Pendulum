# Default configuration for the self-balancing robot

# PID Controller Parameters (easily adjustable)
PID_CONFIG = {
    'P_GAIN': 5.0,     # Proportional gain (how strongly to react to current error)
    'I_GAIN': 0.1,     # Integral gain (how strongly to react to accumulated error)
    'D_GAIN': 1.0,     # Derivative gain (how strongly to react to rate of change)
    'MAX_I_TERM': 20,  # Maximum integral term to prevent windup
    'SETPOINT': 0.0,   # Target angle (0 = balanced upright)
    
    # Motor parameters
    'MOTOR_DEADBAND': 60,  # Motor doesn't move below this value (0-100)
    'MAX_MOTOR_SPEED': 100, # Maximum motor speed (0-100)
    'SAFE_TILT_LIMIT': 45,  # Safety cutoff angle in degrees
    
    # Loop timing
    'SAMPLE_TIME': 0.01,  # Time between PID updates (seconds)
}

# Hardware pin configuration
HARDWARE_CONFIG = {
    'IN1_PIN': 13,  # Motor control pin 1
    'IN2_PIN': 19,  # Motor control pin 2
}

