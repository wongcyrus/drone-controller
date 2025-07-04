#!/usr/bin/env python3
"""
Flask Web Server for Drone Simulator

This server serves the HTML/JS frontend for the drone simulator webapp.
"""

from flask import Flask, render_template, jsonify, request
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.static_folder = 'static'
app.template_folder = 'templates'

# Create templates directory if it doesn't exist
os.makedirs('templates', exist_ok=True)


@app.route('/')
def index():
    """Serve the main simulator page"""
    return render_template('index.html')


@app.route('/api/drones')
def get_drones():
    """API endpoint to get drone information"""
    # This would typically fetch from the WebSocket server
    return jsonify({
        'drones': [],
        'status': 'ok'
    })


@app.route('/api/command', methods=['POST'])
def send_command():
    """API endpoint to send commands to drones"""
    data = request.json
    drone_id = data.get('drone_id')
    command = data.get('command')

    logger.info(f"API command for {drone_id}: {command}")

    # This would typically forward to the drone system
    return jsonify({
        'status': 'ok',
        'message': f'Command sent to {drone_id}: {command}'
    })


def run_web_server(host='localhost', port=8000, debug=False):
    """Run the Flask web server"""
    logger.info(f"Starting web server on http://{host}:{port}")
    app.run(host=host, port=port, debug=debug, threaded=True)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Drone Simulator Web Server')
    parser.add_argument('--host', default='localhost', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8000, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')

    args = parser.parse_args()

    run_web_server(args.host, args.port, args.debug)
