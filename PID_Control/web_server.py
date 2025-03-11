"""
Web dashboard for PID controller - compatibility layer.

This module provides backward compatibility with the original web_server.py
functionality while using the new modular structure in the webpage/ package.
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