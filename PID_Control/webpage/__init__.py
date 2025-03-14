"""
PID Controller Web Dashboard

This package provides a web-based interface for visualizing and tuning 
a PID controller in real-time.
"""

from .web_server import (
    start_server,
    stop_server,
    add_data_point,
    is_server_running,
    PID_PARAMS
)

__all__ = [
    'start_server',
    'stop_server',
    'add_data_point',
    'is_server_running',
    'PID_PARAMS'
] 