import time
from pid_controller import PIDController
from motorController import MotorControl, DualMotorControl

class BalanceController:
    """
    Controller for self-balancing robot that uses PID control.
    Handles the interaction between sensors, PID algorithm, and motor control.
    Supports both single motor and dual motor configurations.
    """
    
    def __init__(self, imu, motor, config):
        """
        Initialize the balance controller.
        
        Args:
            imu: IMU reader object
            motor: Motor controller object (either MotorControl or DualMotorControl)
            config: Configuration dictionary
        """
        self.imu = imu
        self.motor = motor
        self.config = config
        self.pid = PIDController(config)
        self.running = False
        self.last_direction = None
        
        # Determine if we're using dual motors
        self.using_dual_motors = isinstance(self.motor, DualMotorControl)
        if self.using_dual_motors:
            print("Balance controller configured with dual motors")
        else:
            print("Balance controller configured with single motor")
        
    def apply_motor_control(self, output):
        """
        Convert PID output to motor commands.
        
        Args:
            output: PID controller output (-100 to 100)
            
        Returns:
            Motor speed and direction
        """
        # Determine direction based on sign of output
        direction = "clockwise" if output > 0 else "counterclockwise"
        
        # Calculate absolute motor speed
        speed = abs(output)
        
        # Apply deadband compensation with reduced delay for direction changes
        if speed < self.config['MOTOR_DEADBAND']:
            if speed < self.config['MOTOR_DEADBAND'] / 3:  # Reduced threshold for better responsiveness
                # If speed is significantly below deadband, just stop
                if self.using_dual_motors:
                    self.motor.stop_motors()
                else:
                    self.motor.stop_motor()
                return 0, "stopped"
            else:
                # If speed is close to deadband, set it to minimum effective speed
                speed = self.config['MOTOR_DEADBAND']
        
        # Direction change boost - apply extra power momentarily when changing directions
        # to improve responsiveness of the system
        if self.last_direction is not None and direction != self.last_direction and direction != "stopped":
            # Boost the speed by 20% when changing directions to overcome inertia
            # but don't exceed maximum speed
            speed = min(speed * 1.2, self.config['MAX_MOTOR_SPEED'])
        
        # Cap speed at maximum
        speed = min(speed, self.config['MAX_MOTOR_SPEED'])
        
        # Apply to motor(s)
        if self.using_dual_motors:
            self.motor.set_motors_speed(speed, direction)
        else:
            self.motor.set_motor_speed(speed, direction)
        
        # Store direction for next call
        if direction != "stopped":
            self.last_direction = direction
        
        return speed, direction
    
    def start_balancing(self, debug_callback=None):
        """
        Start the balancing control loop.
        
        Args:
            debug_callback: Optional function to call with debug information
        """
        print("\n🤖 Self-Balancing Mode Started!")
        print("Press Ctrl+C to exit")
        print("-------------------------")
        
        # Reset PID controller
        self.pid.reset()
        self.last_direction = None
        
        # Initial time for loop timing
        last_time = time.time()
        self.running = True
        
        try:
            while self.running:
                # Calculate time delta
                current_time = time.time()
                dt = current_time - last_time
                
                # Ensure minimum sample time
                if dt < self.config['SAMPLE_TIME']:
                    time.sleep(self.config['SAMPLE_TIME'] - dt)
                    current_time = time.time()
                    dt = current_time - last_time
                
                # Get IMU data
                imu_data = self.imu.get_imu_data()
                pitch = imu_data['pitch']
                angular_velocity = imu_data['angular_velocity']
                
                # Safety check - stop if tilt is too extreme
                if abs(pitch) > self.config['SAFE_TILT_LIMIT']:
                    print(f"⚠️ Safety cutoff: Tilt {pitch:.2f}° exceeds limit of {self.config['SAFE_TILT_LIMIT']}°")
                    self.motor.stop_motor()
                    break
                
                # Compute PID output
                output = self.pid.compute(pitch, angular_velocity, dt)
                
                # Apply motor control
                speed, direction = self.apply_motor_control(output)
                
                # Create debug info
                debug_info = {
                    'time': current_time,
                    'pitch': pitch,
                    'angular_velocity': angular_velocity,
                    'output': output,
                    'speed': speed,
                    'direction': direction,
                    'pid': self.pid.get_debug_info(),
                }
                
                # Debug info - print every 0.5 seconds
                if int(current_time * 2) != int(last_time * 2):
                    print(f"Pitch: {pitch:.2f}° | AngVel: {angular_velocity:.2f}°/s | "
                          f"Output: {output:.1f} | Motor: {speed:.0f}% {direction}")
                
                # Call debug callback if provided
                if debug_callback:
                    debug_callback(debug_info)
                
                # Update last time
                last_time = current_time
                
        except KeyboardInterrupt:
            print("\nBalancing interrupted by user.")
        
        finally:
            self.stop_balancing()
    
    def stop_balancing(self):
        """Stop the balancing control loop."""
        self.running = False
        self.motor.stop_motor()
        print("Motor stopped. Balance mode exited.") 
