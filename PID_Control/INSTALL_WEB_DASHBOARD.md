# Self-Balancing Robot Web Dashboard

This guide will help you set up the web dashboard for the self-balancing robot.

## Installation

1. Install the required Python packages:

   ```bash
   pip install -r requirements.txt
   ```

2. If you encounter issues with eventlet or Flask-SocketIO, try:

   ```bash
   pip install --upgrade Flask-SocketIO eventlet
   ```

## Usage

1. Start the robot program and select option 6 from the menu:

   ```bash
   python main.py
   ```

2. Choose option 6 "Self-balancing Mode with Web Dashboard"

3. Open the provided URL in your web browser. It will look like:
   
   ```
   http://192.168.x.x:8080
   ```

4. You can access the dashboard from any device on the same network.

## Features

- Real-time graph of robot angle
- Target angle display
- Hidden PID output graph (click on the legend to show)
- Shows the last ~10 seconds of data with automatic scrolling
- Mobile-friendly interface

## Troubleshooting

- **Cannot access the dashboard**: Make sure your device is on the same network as the Raspberry Pi.
- **Graph not updating**: Check that your browser supports WebSockets.
- **Server error**: Check the console output for error messages.

## Customization

The web interface is contained in an HTML template inside the `web_dashboard.py` file. You can modify it to add more features or change the appearance. 