import time

class PIDController:
    """PID Controller for balancing robot."""
    
    def __init__(self, config):
        """
        Initialize PID controller with configuration parameters.
        
        Args:
            config: Dictionary containing PID parameters
        """
        self.kp = config['P_GAIN']         # Proportional gain
        self.ki = config['I_GAIN']         # Integral gain
        self.kd = config['D_GAIN']         # Derivative gain
        self.setpoint = config['SETPOINT'] # Target value
        self.max_i_term = config['MAX_I_TERM']
        
        # PID state variables
        self.prev_error = 0.0
        self.integral = 0.0
        self.prev_time = time.time()
        
        # Variables for debug
        self.p_term = 0.0
        self.i_term = 0.0
        self.d_term = 0.0
        
    def compute(self, current_value, angular_velocity, dt):
        """
        Compute PID control value based on current value and time delta.
        
        Args:
            current_value: Current measured pitch
            angular_velocity: Current angular velocity from IMU
            dt: Time delta since last update in seconds
            
        Returns:
            Control output value (-100 to 100)
        """
        # Calculate error
        error = self.setpoint - current_value
        
        # P term - proportional to current error
        p_term = self.kp * error
        
        # I term - accumulated error over time
        # Increase responsiveness by reducing integral when error changes sign
        if error * self.prev_error < 0:  # Error changed direction
            # Reset part of the integral to reduce overshoot when crossing the setpoint
            self.integral *= 0.5
            
        # Add to integral
        self.integral += error * dt
        
        # Limit integral term to prevent windup
        self.integral = max(-self.max_i_term, min(self.integral, self.max_i_term))
        i_term = self.ki * self.integral
        
        # D term - rate of change of error
        # Using angular velocity directly from IMU instead of calculating derivative
        # as it provides a cleaner signal
        d_term = -self.kd * angular_velocity  # Negative because we want to counter the rotation
        
        # Weighing D term more when angular velocity is high improves responsiveness
        if abs(angular_velocity) > 10:  # If angular velocity is significant
            d_term *= 1.2  # Increase influence of D term
        
        # Calculate total output
        output = p_term + i_term + d_term
        
        # Store current error for next iteration
        self.prev_error = error
        
        # For debugging
        self.p_term = p_term
        self.i_term = i_term
        self.d_term = d_term
        
        return output
    
    def reset(self):
        """Reset the PID controller state."""
        self.prev_error = 0.0
        self.integral = 0.0
        self.prev_time = time.time()
        self.p_term = 0.0
        self.i_term = 0.0
        self.d_term = 0.0
        
    def get_debug_info(self):
        """Return debug information about PID components."""
        return {
            'p_term': self.p_term,
            'i_term': self.i_term,
            'd_term': self.d_term
        }

    def update(self, error, dt, angular_velocity=None):
        """
        Update PID controller with error directly and return output value.
        This is an alternative interface to compute() that takes error directly.
        
        Args:
            error: Error value (setpoint - current_value)
            dt: Time delta since last update in seconds
            angular_velocity: Optional angular velocity from IMU for improved derivative term
            
        Returns:
            Control output value (-100 to 100)
        """
        # P term - proportional to current error
        self.p_term = self.kp * error
        
        # I term - accumulated error over time
        # Increase responsiveness by reducing integral when error changes sign
        if error * self.prev_error < 0:  # Error changed direction
            # Reset part of the integral to reduce overshoot when crossing the setpoint
            self.integral *= 0.5
            
        # Add to integral
        self.integral += error * dt
        
        # Limit integral term to prevent windup
        self.integral = max(-self.max_i_term, min(self.integral, self.max_i_term))
        self.i_term = self.ki * self.integral
        
        # D term - either use angular velocity (preferred) or calculate derivative from error
        if angular_velocity is not None:
            # Using angular velocity directly from IMU gives cleaner signal
            self.d_term = -self.kd * angular_velocity  # Negative because we want to counter the rotation
            
            # Weighing D term more when angular velocity is high improves responsiveness
            if abs(angular_velocity) > 10:  # If angular velocity is significant
                self.d_term *= 1.2  # Increase influence of D term
        else:
            # Fall back to raw error derivative when angular velocity is not available
            derivative = (error - self.prev_error) / dt
            self.d_term = self.kd * derivative
        
        # Save error for next iteration
        self.prev_error = error
        
        # Calculate output
        output = self.p_term + self.i_term + self.d_term
        
        # Limit output to range (-100 to 100)
        output = max(-100, min(output, 100))
        
        return output 
