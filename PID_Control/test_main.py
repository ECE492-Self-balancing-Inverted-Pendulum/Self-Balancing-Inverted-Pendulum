#!/usr/bin/env python3
"""
Test script for the runtime_parameter_tuning mode in main.py
"""
import os
import sys
import time

class MockIMUReader:
    """Mock IMU reader for testing"""
    def __init__(self, alpha=0.3, upside_down=True):
        self.ALPHA = alpha
        self.upside_down = upside_down
        self.angle = 0.0
        self.direction = 1
        
    def get_imu_data(self):
        """Get mock IMU data"""
        # Update angle in a sine-wave like pattern
        self.angle += self.direction * 0.1
        if abs(self.angle) > 10:
            self.direction *= -1
            
        return {
            'roll': self.angle,
            'pitch': 0.0,
            'yaw': 0.0,
            'angular_velocity': self.direction * 2.0
        }
        
    def imu_tuning_mode(self):
        """Mock tuning mode"""
        print("Mock IMU tuning mode")

class MockBalanceController:
    """Mock balance controller for testing"""
    def __init__(self, imu, motor, config):
        self.imu = imu
        self.motor = motor
        self.config = config
        self.sample_time = config.get('SAMPLE_TIME', 0.01)
        self.p_term = 0.0
        self.i_term = 0.0
        self.d_term = 0.0
        self.running = False
        
    def start_balancing(self, debug_callback=None):
        """Start mock balancing"""
        print("\n🤖 Mock Self-Balancing Mode Started!")
        print("Press 'Q' to exit")
        
        self.running = True
        i = 0
        
        try:
            while self.running and i < 300:  # Run for 300 iterations max
                # Get IMU data
                imu_data = self.imu.get_imu_data()
                roll = imu_data['roll']
                angular_velocity = imu_data['angular_velocity']
                
                # Calculate mock PID components
                self.p_term = self.config.get('P_GAIN', 1.0) * roll
                self.i_term = self.config.get('I_GAIN', 0.1) * roll * 0.5
                self.d_term = self.config.get('D_GAIN', 0.01) * angular_velocity
                
                pid_output = self.p_term + self.i_term + self.d_term
                motor_output = min(100, abs(pid_output))
                
                # Call debug callback if provided
                if debug_callback:
                    debug_info = {
                        'roll': roll,
                        'angular_velocity': angular_velocity,
                        'output': pid_output,
                        'motor_output': motor_output,
                        'pid': {
                            'p_term': self.p_term,
                            'i_term': self.i_term,
                            'd_term': self.d_term
                        }
                    }
                    debug_callback(debug_info)
                
                # Print status every 10 iterations
                if i % 10 == 0:
                    print(f"Roll: {roll:.2f}° | Angular Vel: {angular_velocity:.2f}°/s | Output: {pid_output:.2f} | Motor: {motor_output:.2f}%")
                
                time.sleep(self.sample_time)
                i += 1
                
                # Check for keyboard input (non-blocking)
                if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                    key = sys.stdin.read(1)
                    if key.lower() == 'q':
                        print("\nStopping mock self-balancing mode...")
                        break
        except KeyboardInterrupt:
            print("\nMock balancing interrupted")
        finally:
            self.running = False
            print("\nMock self-balancing mode stopped")
    
    def stop_balancing(self):
        """Stop mock balancing"""
        self.running = False
        
    def update_from_config(self, config):
        """Update mock controller from config"""
        self.config = config
        self.sample_time = config.get('SAMPLE_TIME', 0.01)
        return True

def main():
    """Test the runtime_parameter_tuning function"""
    print("Testing runtime_parameter_tuning...")
    
    # Add directory to path
    sys.path.insert(0, os.path.abspath('.'))
    
    # Import the config
    from config import CONFIG, HARDWARE_CONFIG
    
    # Create mock objects
    imu = MockIMUReader(
        alpha=CONFIG.get('IMU_FILTER_ALPHA', 0.3),
        upside_down=CONFIG.get('IMU_UPSIDE_DOWN', True)
    )
    
    # Import after potential mocking
    from motorController import DualMotorControl
    
    # Create motor controller
    motors = DualMotorControl(
        motor_a_in1=HARDWARE_CONFIG['MOTOR_A_IN1_PIN'],
        motor_a_in2=HARDWARE_CONFIG['MOTOR_A_IN2_PIN'],
        motor_b_in1=HARDWARE_CONFIG['MOTOR_B_IN1_PIN'],
        motor_b_in2=HARDWARE_CONFIG['MOTOR_B_IN2_PIN']
    )
    
    # Create mock balance controller
    balance_controller = MockBalanceController(imu, motors, CONFIG)
    
    # Import the function to test
    from main import runtime_parameter_tuning
    
    # Override select.select for non-blocking input in the balance controller
    import select
    original_select = select.select
    
    def mock_select(rlist, wlist, xlist, timeout=None):
        return [], [], []
    
    select.select = mock_select
    
    try:
        # Run the function
        runtime_parameter_tuning(None, balance_controller)
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    finally:
        # Restore select
        select.select = original_select
        
        # Clean up
        try:
            from webpage import stop_server
            stop_server()
        except:
            pass

if __name__ == "__main__":
    main() 