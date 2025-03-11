"""
Route definitions for the PID controller web dashboard.
"""
from flask import render_template, jsonify, request
from .config import WEB_CONFIG, DATA_LOCK
from .data_manager import get_data_for_display, clear_data

def register_routes(app):
    """
    Register all routes with the Flask application
    
    Args:
        app: Flask application instance
    """
    
    @app.route('/')
    def index():
        """Serve the main page"""
        return render_template('index.html', config=WEB_CONFIG)

    @app.route('/data')
    def get_data():
        """API endpoint to get the current PID data"""
        return jsonify(get_data_for_display())

    @app.route('/config', methods=['GET', 'POST'])
    def config():
        """API endpoint to get or update configuration"""
        if request.method == 'POST':
            data = request.get_json()
            with DATA_LOCK:
                if 'time_window' in data:
                    WEB_CONFIG['time_window'] = int(data['time_window'])
                if 'update_interval' in data:
                    WEB_CONFIG['update_interval'] = int(data['update_interval'])
                if 'csv_logging' in data:
                    WEB_CONFIG['csv_logging'] = bool(data['csv_logging'])
            return jsonify({"status": "success"})
        else:
            return jsonify(WEB_CONFIG)

    @app.route('/pid_params', methods=['GET', 'POST'])
    def pid_params():
        """API endpoint to get or update PID parameters"""
        # Import here to avoid circular imports
        from config import CONFIG, save_config
        
        if request.method == 'POST':
            data = request.get_json()
            updated = False
            
            # Update the configuration
            if 'p_gain' in data:
                CONFIG['P_GAIN'] = float(data['p_gain'])
                updated = True
            if 'i_gain' in data:
                CONFIG['I_GAIN'] = float(data['i_gain'])
                updated = True
            if 'd_gain' in data:
                CONFIG['D_GAIN'] = float(data['d_gain'])
                updated = True
            if 'alpha' in data:
                CONFIG['IMU_FILTER_ALPHA'] = float(data['alpha'])
                updated = True
            if 'direction_change_boost' in data:
                CONFIG['DIRECTION_CHANGE_BOOST'] = float(data['direction_change_boost'])
                updated = True
            if 'sample_time' in data:
                CONFIG['SAMPLE_TIME'] = float(data['sample_time'])
                updated = True
                
            # Save the configuration if it was updated
            if updated:
                save_config(CONFIG)
                
            return jsonify({"status": "success"})
        else:
            from config import CONFIG
            # Return the current PID parameters
            return jsonify({
                'p_gain': CONFIG.get('P_GAIN', 0),
                'i_gain': CONFIG.get('I_GAIN', 0),
                'd_gain': CONFIG.get('D_GAIN', 0),
                'alpha': CONFIG.get('IMU_FILTER_ALPHA', 0.3),
                'direction_change_boost': CONFIG.get('DIRECTION_CHANGE_BOOST', 20.0),
                'sample_time': CONFIG.get('SAMPLE_TIME', 0.01)
            })

    @app.route('/restart_pid', methods=['POST'])
    def restart_pid():
        """API endpoint to restart the PID controller"""
        # Notify the main thread to restart the PID controller
        WEB_CONFIG['restart_requested'] = True
        
        # Clear the data
        clear_data()
        
        return jsonify({"status": "success"}) 