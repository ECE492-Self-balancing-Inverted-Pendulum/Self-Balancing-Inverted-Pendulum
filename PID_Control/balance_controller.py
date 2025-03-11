import time
import sys
import select
import termios
import tty
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
        self.enable_debug = True  # Enable debug output by default
        
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
            # Get boost percentage from config (default to 20% if not present)
            boost_percent = self.config.get('DIRECTION_CHANGE_BOOST', 20.0)
            # Apply boost but don't exceed maximum speed
            boost_multiplier = 1.0 + (boost_percent / 100.0)
            speed = min(speed * boost_multiplier, self.config['MAX_MOTOR_SPEED'])
        
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
        print("Press 'Q' to return to main menu")
        print("-------------------------")
        
        # Reset PID controller
        self.pid.reset()
        self.last_direction = None
        
        # Initial time for loop timing
        last_time = time.time()
        self.running = True
        
        # Setup for non-blocking input detection
        old_settings = None
        if sys.stdin.isatty():
            old_settings = termios.tcgetattr(sys.stdin)
            tty.setraw(sys.stdin.fileno())
        
        # For tracking debug output timing
        last_debug_time = 0
        
        try:
            while self.running:
                # Check for 'Q' keypress to exit
                if sys.stdin.isatty() and select.select([sys.stdin], [], [], 0.0)[0]:
                    key = sys.stdin.read(1)
                    if key.lower() == 'q':
                        print("\nReturning to main menu...")
                        self.running = False
                        break
                
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
                roll = imu_data['roll']
                angular_velocity = imu_data['angular_velocity']
                
                # Safety check - stop if tilt is too extreme
                if abs(roll) > self.config['SAFE_TILT_LIMIT']:
                    print(f"⚠️ Safety cutoff: Tilt {roll:.2f}° exceeds limit of {self.config['SAFE_TILT_LIMIT']}°")
                    if self.using_dual_motors:
                        self.motor.stop_motors()
                    else:
                        self.motor.stop_motor()
                    break
                
                # Compute PID output
                output = self.pid.compute(roll, angular_velocity, dt)
                
                # Apply motor control
                speed, direction = self.apply_motor_control(output)
                
                # Create debug info
                debug_info = {
                    'time': current_time,
                    'roll': roll,
                    'angular_velocity': angular_velocity,
                    'output': output,
                    'speed': speed,
                    'direction': direction,
                    'pid': self.pid.get_debug_info(),
                }
                
                # Send data to web interface through callback - always call if provided
                if debug_callback:
                    debug_callback(debug_info)
                
                # Print debug info to console less frequently to avoid overwhelming
                if self.enable_debug and current_time - last_debug_time > 0.5:  # Print every 0.5 seconds
                    print(f"\rRoll: {roll:.2f}° | AngVel: {angular_velocity:.2f}°/s | Output: {output:.1f} | Motor: {speed:.0f}% {direction}", end="")
                    last_debug_time = current_time
                
                # Update last time
                last_time = current_time
                
        except Exception as e:
            print(f"Error in balancing loop: {e}")
        finally:
            # Clean up
            if self.using_dual_motors:
                self.motor.stop_motors()
            else:
                self.motor.stop_motor()
            
            # Restore terminal settings
            if old_settings is not None:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
    
    def stop_balancing(self):
        """Stop the balancing control loop."""
        self.running = False
        if self.using_dual_motors:
            self.motor.stop_motors()
        else:
            self.motor.stop_motor()
        print("Motor stopped. Balance mode exited.") 
