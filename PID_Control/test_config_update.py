#!/usr/bin/env python3
"""
Test script to verify PID parameter updates are properly written to the config file.

Usage:
    python test_config_update.py [--test] [--fix-config] [--check-permissions]

Options:
    --test              Run the PID update test
    --fix-config        Fix the config file (ensure it has the correct keys)
    --check-permissions Check if the config file has the correct permissions
"""

import json
import time
import os
import requests
import socketio
import threading
import sys
import argparse

# Import the config module
from config import CONFIG_FILE, load_config, save_config, DEFAULT_CONFIG
from web_dashboard import app, socketio as server_socketio, start_server, stop_server

# Port to use for the test server
TEST_PORT = 8081

def check_file_permissions():
    """Check if the config file exists and has proper permissions."""
    # Check if file exists
    if not os.path.exists(CONFIG_FILE):
        print(f"❌ Config file {CONFIG_FILE} does not exist.")
        return False
    
    # Check if file is readable
    if not os.access(CONFIG_FILE, os.R_OK):
        print(f"❌ Config file {CONFIG_FILE} is not readable.")
        return False
    
    # Check if file is writable
    if not os.access(CONFIG_FILE, os.W_OK):
        print(f"❌ Config file {CONFIG_FILE} is not writable.")
        print(f"Try running: chmod 666 {CONFIG_FILE}")
        return False
    
    # Check owner and permissions
    file_stats = os.stat(CONFIG_FILE)
    print(f"Config file owner: {file_stats.st_uid}, Permissions: {oct(file_stats.st_mode)[-3:]}")
    
    # Additional check - try writing to the file
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
        
        # Write the same content back (no changes)
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
        
        print(f"✅ Config file {CONFIG_FILE} is readable and writable.")
        return True
    except Exception as e:
        print(f"❌ Error accessing config file: {e}")
        return False

def fix_config_file():
    """
    Fix the config file by ensuring it has the correct keys.
    - Ensures target_angle is present instead of SETPOINT
    - Makes sure all required keys from DEFAULT_CONFIG are present
    """
    try:
        if not os.path.exists(CONFIG_FILE):
            print(f"Config file {CONFIG_FILE} does not exist. Creating it with default values.")
            save_config(DEFAULT_CONFIG)
            return True
        
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
        
        # Check if we need to convert SETPOINT to target_angle
        if 'SETPOINT' in config and 'target_angle' not in config:
            print("Converting SETPOINT to target_angle")
            config['target_angle'] = config.pop('SETPOINT')
            changed = True
        else:
            changed = False
        
        # Ensure all default keys are present
        for key, value in DEFAULT_CONFIG.items():
            if key not in config:
                if key != 'SETPOINT':  # Skip SETPOINT as we use target_angle
                    print(f"Adding missing key: {key}")
                    config[key] = value
                    changed = True
        
        # If we made changes, save the file
        if changed:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=4)
            print("✅ Config file fixed successfully.")
        else:
            print("✅ Config file already has the correct format.")
        
        return True
    except Exception as e:
        print(f"❌ Error fixing config file: {e}")
        return False

def test_pid_update():
    """Test updating PID parameters."""
    # First check file permissions
    if not check_file_permissions():
        print("Fixing permissions...")
        try:
            os.chmod(CONFIG_FILE, 0o666)  # Read/write for everyone
            if not check_file_permissions():
                print("Failed to fix permissions. Please fix manually.")
                return
        except Exception as e:
            print(f"Failed to fix permissions: {e}")
            print(f"Please run: chmod 666 {CONFIG_FILE}")
            return
    
    # Start the server in a separate thread
    server_thread = threading.Thread(target=start_server, args=('127.0.0.1', TEST_PORT))
    server_thread.daemon = True
    server_thread.start()
    
    # Give the server time to start
    time.sleep(2)
    
    # Original values - load from config file
    try:
        with open(CONFIG_FILE, 'r') as f:
            original_config = json.load(f)
        
        print(f"Original config: {original_config}")
        original_p = original_config.get('P_GAIN', 0)
        original_i = original_config.get('I_GAIN', 0)
        original_d = original_config.get('D_GAIN', 0)
        
        # Create a Socket.IO client
        client = socketio.Client()
        client.connect(f'http://127.0.0.1:{TEST_PORT}')
        
        # New test values - significantly different to make verification clear
        new_p = original_p + 1.0 if original_p < 9.0 else original_p - 1.0
        new_i = original_i + 0.5 if original_i < 9.5 else original_i - 0.5
        new_d = original_d + 1.5 if original_d < 8.5 else original_d - 1.5
        
        print(f"Updating PID parameters to: P={new_p}, I={new_i}, D={new_d}")
        
        # Send PID update via Socket.IO
        client.emit('update_pid', {
            'p_gain': new_p,
            'i_gain': new_i,
            'd_gain': new_d
        })
        
        # Give the server time to process the update
        time.sleep(2)
        
        # Read the config file again to verify changes
        with open(CONFIG_FILE, 'r') as f:
            updated_config = json.load(f)
        
        print(f"Updated config: {updated_config}")
        
        # Check if the values were updated correctly
        updated_p = updated_config.get('P_GAIN', 0)
        updated_i = updated_config.get('I_GAIN', 0)
        updated_d = updated_config.get('D_GAIN', 0)
        
        if abs(updated_p - new_p) < 0.001 and abs(updated_i - new_i) < 0.001 and abs(updated_d - new_d) < 0.001:
            print("✅ TEST PASSED: PID parameters were correctly updated in the config file")
        else:
            print("❌ TEST FAILED: PID parameters were not updated correctly")
            print(f"Expected: P={new_p}, I={new_i}, D={new_d}")
            print(f"Actual: P={updated_p}, I={updated_i}, D={updated_d}")
        
        # Disconnect the client
        client.disconnect()
        
        # Restore original values if needed
        # save_config(original_config)
        
    except Exception as e:
        print(f"❌ TEST ERROR: {e}")
    finally:
        # Stop the server
        stop_server()

def main():
    """Main function to handle command line arguments."""
    parser = argparse.ArgumentParser(description='Test and fix PID config file issues')
    parser.add_argument('--test', action='store_true', help='Run the PID update test')
    parser.add_argument('--fix-config', action='store_true', help='Fix the config file format')
    parser.add_argument('--check-permissions', action='store_true', help='Check file permissions')
    
    args = parser.parse_args()
    
    # If no arguments, show help
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    
    # Check permissions if requested
    if args.check_permissions:
        check_file_permissions()
    
    # Fix config if requested
    if args.fix_config:
        fix_config_file()
    
    # Run test if requested
    if args.test:
        test_pid_update()

if __name__ == "__main__":
    main()
