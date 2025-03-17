#!/usr/bin/env python3
"""
Test script for the web server
"""
import sys
import os
import time

# Make sure we use the mock motor controller
print("Setting up test environment...")
sys.path.insert(0, os.path.abspath('.'))
if os.path.exists('motorController_mock.py'):
    print("Using mock motor controller")
    with open('motorController.py.bak', 'w') as f:
        with open('motorController.py', 'r') as src:
            f.write(src.read())
    with open('motorController.py', 'w') as f:
        with open('motorController_mock.py', 'r') as src:
            f.write(src.read())

# Import after replacing the motor controller
print("Trying to import from webpage...")
try:
    from webpage import start_server, stop_server, add_data_point, set_pid_params
    web_import_source = "webpage"
    print("Successfully imported from webpage package")
except ImportError as e:
    print(f"ImportError from webpage: {e}")
    try:
        print("Trying to import from web_server...")
        from web_server import start_server, stop_server, add_data_point, set_pid_params
        web_import_source = "web_server"
        print("Successfully imported from web_server module")
    except ImportError as e:
        print(f"ImportError from web_server: {e}")
        print("Web server functionality not available")
        sys.exit(1)

# Import the config
try:
    from config import CONFIG
    print("Successfully imported CONFIG")
except ImportError as e:
    print(f"ImportError from config: {e}")
    CONFIG = {
        'P_GAIN': 1.0,
        'I_GAIN': 0.1,
        'D_GAIN': 0.01,
        'ZERO_THRESHOLD': 0.1
    }
    print("Using default CONFIG")

def main():
    """Start the web server and generate some test data"""
    port = 8080
    
    print(f"Starting web server on port {port}...")
    try:
        # Start the server
        start_server(port=port)
        print(f"Web server started on port {port}")
        
        # Set initial PID params
        print("Setting initial PID parameters...")
        set_pid_params(
            CONFIG.get('P_GAIN', 1.0),
            CONFIG.get('I_GAIN', 0.1),
            CONFIG.get('D_GAIN', 0.01),
            0.0  # Target angle is always 0 for balancing
        )
        
        print("\n---------------------------------------")
        print(f"WEB DASHBOARD: http://localhost:{port}")
        print("---------------------------------------\n")
        
        # Generate test data
        print("Generating test data - press Ctrl+C to stop")
        angle = 0.0
        direction = 1
        i = 0
        
        while True:
            # Update angle in a sine-wave like pattern
            angle += direction * 0.1
            if abs(angle) > 10:
                direction *= -1
            
            # P, I, D components
            p_term = CONFIG.get('P_GAIN', 1.0) * angle
            i_term = CONFIG.get('I_GAIN', 0.1) * angle * 0.5  # Simulated i_term
            d_term = CONFIG.get('D_GAIN', 0.01) * 2 if direction > 0 else -2  # Simulated d_term
            
            # Total PID output
            pid_output = p_term + i_term + d_term
            
            # Send data to dashboard
            add_data_point(
                actual_angle=angle,
                target_angle=0.0,
                error=-angle,
                p_term=p_term,
                i_term=i_term,
                d_term=d_term,
                pid_output=pid_output,
                motor_output=abs(pid_output)
            )
            
            # Print progress
            if i % 10 == 0:
                print(f"Sent data point: angle={angle:.2f}, output={pid_output:.2f}")
            
            i += 1
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\nStopping server...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Stop the server
        try:
            stop_server()
            print("Server stopped")
        except:
            print("Error stopping server")
        
        # Restore the original motor controller
        if os.path.exists('motorController.py.bak'):
            print("Restoring original motor controller")
            with open('motorController.py', 'w') as f:
                with open('motorController.py.bak', 'r') as src:
                    f.write(src.read())
            os.remove('motorController.py.bak')

if __name__ == "__main__":
    main() 