"""
Web Dashboard for Self-Balancing Robot - Compatibility Layer

This module provides a bridge between the main application and the webpage package,
which implements a web-based dashboard for monitoring and tuning the self-balancing robot.

Key features:
- Real-time visualization of robot angle, target, and PID outputs
- Interactive adjustment of PID parameters during runtime
- Data logging to CSV for post-run analysis
- Responsive web interface accessible from any device on the same network

This compatibility layer maintains backward compatibility with older code while
using the newer modular structure in the webpage/ package.

Example Usage:
    # Start the web server
    from web_server import start_server, add_data_point
    
    # Start the server on the default port (8080)
    start_server()
    
    # Or specify a different port
    start_server(port=5000)
    
    # Send data to the dashboard in your main loop
    while True:
        # Get data from your sensors and control system
        angle = get_current_angle()
        target = 0.0  # Target angle for balancing is typically 0
        pid_output = calculate_pid_output()
        
        # Send data to the dashboard
        add_data_point(
            actual_angle=angle,
            target_angle=target,
            error=target - angle,
            p_term=p_component,
            i_term=i_component,
            d_term=d_component,
            pid_output=pid_output
        )
        
        time.sleep(0.01)  # Control loop delay
    
    # When done, stop the server
    stop_server()
"""

# Import all required functions from the new modular package
from webpage import add_data_point, start_server, stop_server
from webpage.data_manager import clear_csv_file
from webpage.static_generator import setup_static_files

# Re-export all functions with the same names for backward compatibility
__all__ = ['add_data_point', 'start_server', 'stop_server', 
           'clear_csv_file', 'create_static_files', 'create_templates']

# Alias functions to maintain compatibility
create_static_files = setup_static_files
create_templates = setup_static_files  # Both functions are now handled by setup_static_files

# Execute setup if this file is run directly
if __name__ == "__main__":
    # Create necessary files and start the server in debug mode
    setup_static_files()
    start_server(debug=True) 