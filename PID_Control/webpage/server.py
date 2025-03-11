"""
Server management for the PID controller web dashboard.
Handles starting and stopping the Flask web server.
"""
import threading
from .app import create_app
from .config import WEB_CONFIG
from .data_manager import clear_csv_file
from .static_generator import setup_static_files

def start_server(host='0.0.0.0', port=5000, debug=False):
    """
    Start the Flask server in a separate thread
    
    Args:
        host: Host address to bind to
        port: Port to listen on
        debug: Whether to run in debug mode
    """
    # Ensure static files are present
    setup_static_files()
    
    # Clear the CSV file
    clear_csv_file()
    
    # Create the Flask app
    app = create_app()
    
    # Start the server
    WEB_CONFIG['is_running'] = True
    
    # Start the server in a daemon thread so it will terminate when the main program exits
    server_thread = threading.Thread(
        target=lambda: app.run(host=host, port=port, debug=debug, use_reloader=False),
        daemon=True
    )
    server_thread.start()
    
    print(f"Web dashboard started at http://{host if host != '0.0.0.0' else 'localhost'}:{port}")
    
def stop_server():
    """
    Stop the Flask server
    Note: This only marks the server as not running, 
    the actual shutdown happens when the main program exits
    """
    WEB_CONFIG['is_running'] = False
    print("Web server stopped.") 