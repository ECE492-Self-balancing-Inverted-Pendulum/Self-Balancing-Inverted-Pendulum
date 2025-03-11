"""
PID Controller Web Interface

This package provides a web-based dashboard for visualizing and controlling a PID controller.
"""

import threading
import time
import logging
from .app import create_app, add_data_point, set_pid_params, update_pid_params, set_update_callback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('pid_web_dashboard')

# Create a global Flask app instance
app = None
server_thread = None
server_started = False

def start_server(host='0.0.0.0', port=5000, debug=False, use_reloader=False):
    """
    Start the Flask web server in a separate thread
    
    Args:
        host (str): The host address to bind to
        port (int): The port to bind to
        debug (bool): Whether to run Flask in debug mode
        use_reloader (bool): Whether to use the Flask reloader
    """
    global app, server_thread, server_started
    
    # Prevent starting multiple servers
    if server_started and server_thread and server_thread.is_alive():
        logger.info("Server is already running")
        return
    
    try:
        # Create Flask app if it doesn't exist
        if app is None:
            app = create_app()
            logger.info("Flask app created")
        
        # Start the server in a separate thread
        def run_server():
            try:
                logger.info(f"Starting Flask server on {host}:{port}")
                app.run(host=host, port=port, debug=debug, use_reloader=use_reloader)
            except Exception as e:
                logger.error(f"Error in Flask server: {e}")
                server_started = False
        
        server_thread = threading.Thread(target=run_server)
        server_thread.daemon = True  # Daemonize thread
        server_thread.start()
        server_started = True
        
        # Wait a moment to ensure the server starts
        time.sleep(0.5)
        
        logger.info(f"Web server started at http://{host}:{port}")
        print(f"Web dashboard available at http://{host}:{port}")
    except Exception as e:
        logger.error(f"Error starting web server: {e}")
        print(f"Error starting web server: {e}")
        server_started = False

def stop_server():
    """Stop the Flask web server"""
    global server_thread, server_started
    
    if server_thread and server_thread.is_alive():
        logger.info("Shutting down web server...")
        # In a real implementation, we would use werkzeug's shutdown function
        # but for now, we'll just set the flag to indicate it's no longer running
        server_started = False
        server_thread = None
        logger.info("Web server stopped")
        print("Web server stopped")

def is_server_running():
    """Check if the web server is running"""
    global server_thread, server_started
    return server_started and server_thread and server_thread.is_alive()

# Export key functions
__all__ = [
    'start_server', 'stop_server', 'add_data_point', 
    'set_pid_params', 'update_pid_params', 'set_update_callback',
    'is_server_running'
] 