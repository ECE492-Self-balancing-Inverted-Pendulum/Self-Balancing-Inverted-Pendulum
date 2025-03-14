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
            Tuple of (output, speed, direction)
        """
        # Determine direction based on sign of output
        if output > 0:
            direction = "clockwise"
        else:
            direction = "counterclockwise"
        
        # Take absolute value for speed
        speed = abs(output)
        
        # Apply motor deadband
        if speed < self.config['MOTOR_DEADBAND']:
            speed = 0
            direction = "stop"
        
        # Apply boost when changing direction to overcome inertia
        if self.last_direction != direction and direction != "stop":
            # Add a boost when changing direction to overcome inertia
            boost_percent = self.config.get('DIRECTION_CHANGE_BOOST', 20)
            speed = min(100, speed * (1 + boost_percent / 100.0))
        
        # Save current direction for next iteration
        if direction != "stop":
            self.last_direction = direction
        
        # Set motor speed based on whether we're using dual motors or single
        if self.using_dual_motors:
            self.motor.set_motors_speed(speed, direction)
        else:
            self.motor.set_motor_speed(speed, direction)
        
        return output, speed, direction
    
    def start_balancing(self, debug_callback=None):
        """
        Start the self-balancing control loop.
        
        Args:
            debug_callback: Optional callback function for debugging and visualization
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
                        # Clear line before printing to avoid text overlap
                        sys.stdout.write('\r' + ' ' * 80)
                        sys.stdout.flush()
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
                    # Clear line before printing to avoid text overlap
                    sys.stdout.write('\r' + ' ' * 80)
                    sys.stdout.flush()
                    print(f"\n⚠️ Safety cutoff: Tilt {roll:.2f}° exceeds limit of {self.config['SAFE_TILT_LIMIT']}°")
                    if self.using_dual_motors:
                        self.motor.stop_motors()
                    else:
                        self.motor.stop_motor()
                    self.running = False
                    break
                
                # Update PID controller
                pid_update = self.pid.update(0.0 - roll, dt, angular_velocity)  # Pass angular velocity for better D term
                
                # Apply motor control based on PID output
                output, speed, direction = self.apply_motor_control(pid_update)
                
                # Update last time for next iteration
                last_time = current_time
                
                # Call debug callback if provided
                if debug_callback and callable(debug_callback):
                    # Prepare debug info
                    debug_info = {
                        'roll': roll,
                        'angular_velocity': angular_velocity,
                        'output': output,
                        'pid': {
                            'p_term': self.pid.p_term,
                            'i_term': self.pid.i_term,
                            'd_term': self.pid.d_term
                        }
                    }
                    
                    # Call the debug callback with the info
                    debug_callback(debug_info)
                    
                # Print debug output directly to terminal if no callback and debug is enabled
                elif self.enable_debug:
                    # Limit debug output rate to avoid flooding terminal
                    if current_time - last_debug_time > 0.1:  # Max 10 updates per second
                        # Clear the line completely before writing
                        sys.stdout.write('\r' + ' ' * 80)
                        sys.stdout.write(f"\rAngle: {roll:6.2f}° | Output: {output:6.1f} | P: {self.pid.p_term:6.1f} | I: {self.pid.i_term:6.1f} | D: {self.pid.d_term:6.1f}")
                        sys.stdout.flush()
                        last_debug_time = current_time
        
        except Exception as e:
            print(f"\nError in balancing loop: {e}")
        
        finally:
            # Restore terminal settings
            if old_settings:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
            
            # Stop motors for safety
            if self.using_dual_motors:
                self.motor.stop_motors()
            else:
                self.motor.stop_motor()
            
            print("\nBalancing stopped.")
    
    def stop_balancing(self):
        """Stop the balancing control loop."""
        self.running = False
        if self.using_dual_motors:
            self.motor.stop_motors()
        else:
            self.motor.stop_motor()
        print("Motor stopped. Balance mode exited.") 
