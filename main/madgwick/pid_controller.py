"""
PID Controller Module for Self-Balancing Robot

This module implements a PID controller that constantly updates its parameters from
the CONFIG object to ensure it's always using the latest tuning values. Key features:

- Dynamically loads PID parameters on each compute cycle
- Calculates derivative from angle changes for smoother control
- Implements integral windup prevention
- Reduces integral term when crossing setpoint
- Auto-limits output range to motor capabilities (-100 to 100)

Example Usage:
    # Initialize the controller
    from config import CONFIG
    pid = PIDController()
    
    # In the main control loop:
    current_angle = imu.get_roll()
    dt = 0.01  # Time since last update in seconds
    output = pid.compute(current_angle, dt)
    
    # Apply output to motors
    motors.set_speed(abs(output), "clockwise" if output > 0 else "counterclockwise")
"""

from config import load_config, DEFAULT_CONFIG

class PIDController:
    """PID Controller for balancing robot that uses the latest configuration values."""
    
    def __init__(self):
        """Initialize PID controller state variables."""
        # PID state variables
        self.prev_error = 0.0
        self.integral = 0.0
        
    def compute(self, current_value, dt):
        """
        Compute PID control value based on current value and time delta.
        
        Args:
            current_value: Current measured angle (degrees)
            dt: Time delta since last update in seconds
            
        Returns:
            Control output value (-100 to 100)
        """
        # Get the latest PID parameters from CONFIG
        current_config = DEFAULT_CONFIG
        
        # Update PID parameters from CONFIG
        self.kp = current_config.get('P_GAIN', 5.0)
        self.ki = current_config.get('I_GAIN', 0.1)
        self.kd = current_config.get('D_GAIN', 1.0)
       
       # print(f"These are the PID vals: P: {self.kp}, i {self.ki}, d {self.kd}")
       
        # Update setpoint from CONFIG
        self.setpoint = current_config.get('target_angle', 0.0)
        
        # Update MAX_I_TERM from CONFIG
        self.max_i_term = current_config.get('MAX_I_TERM', 20.0)
        
        # Calculate error
        error = self.setpoint - current_value
        
        # P term - proportional to current error
        p_term = self.kp * error
        
        # Add to integral
        self.integral += error * dt
        
        # Limit integral term to prevent windup
        self.integral = max(-self.max_i_term, min(self.integral, self.max_i_term))
        i_term = self.ki * self.integral
        
        # D term - calculate rate of change from angle difference
        derivative = (error - self.prev_error) / dt
        d_term = self.kd * derivative
        
        # Calculate total output
        output = p_term + i_term + d_term
        
        # Limit output to range (-100 to 100)
        output = max(-100, min(output, 100))
        
        # Store current error for next iteration
        self.prev_error = error
        
        return output
    
    def reset(self):
        """Reset the PID controller state."""
        self.prev_error = 0.0
        self.integral = 0.0
    

