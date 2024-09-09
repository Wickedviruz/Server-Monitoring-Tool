from GUI import app, socketio
from flask import render_template, request, redirect, url_for, jsonify
from flask_socketio import emit
import psutil
import platform
import socket
import time
import os
from threading import Thread
from datetime import datetime

hostname = socket.gethostname()
start_time = time.time()

# Hardcoded user for login (you can replace this with a database lookup)
users = {'admin': 'password'}

# Keep track of the last network IO data
last_net_io = psutil.net_io_counters()
last_time = time.time()

process_cache = {
    "data": [],
    "timestamp": 0
}

CACHE_TIMEOUT = 10  # Cache timeout in seconds

LOG_FILE_PATH = os.path.join(os.path.dirname(__file__), '..', 'server_monitor.log')


# Function to get system info
def get_system_info():
    global last_net_io, last_time

    # System information
    operating_system = platform.system()
    kernel_version = platform.release()
    cpu_info = platform.processor()
    num_of_cores = psutil.cpu_count(logical=True)
    total_memory = psutil.virtual_memory().total / (1024 ** 3)  # GB
    uptime = time.time() - psutil.boot_time()
    num_processes = len(psutil.pids())

    # CPU and memory usage
    cpu_usage = psutil.cpu_percent(interval=1)
    memory_usage = psutil.virtual_memory().percent

    # Network speed (calculate over time)
    current_net_io = psutil.net_io_counters()
    current_time = time.time()

    time_diff = current_time - last_time
    if time_diff > 0:
        upload_speed_mbps = ((current_net_io.bytes_sent - last_net_io.bytes_sent) * 8) / (1024 * 1024 * time_diff)
        download_speed_mbps = ((current_net_io.bytes_recv - last_net_io.bytes_recv) * 8) / (1024 * 1024 * time_diff)
    else:
        upload_speed_mbps = 0
        download_speed_mbps = 0

    # Update last_net_io and last_time for the next calculation
    last_net_io = current_net_io
    last_time = current_time

    # Versions (hardcoded for this example)
    server_monitoring_version = "1.0.0"
    gui_version = "1.0.0"

    # Current time and date on the system (the clock)
    current_time_str = datetime.now().strftime('%Y:%m:%d %H:%M:%S')

    return {
        'hostname': hostname,
        'operating_system': f"{operating_system} {kernel_version}",
        'cpu_info': f"{cpu_info} ({num_of_cores} cores)",
        'total_memory': f"{total_memory:.2f} GB",
        'uptime': time.strftime('%H:%M:%S', time.gmtime(uptime)),
        'num_processes': num_processes,
        'cpu_usage': cpu_usage,  # Send CPU usage
        'memory_usage': memory_usage,  # Send Memory usage
        'upload_speed': upload_speed_mbps,  # Send upload speed in Mbps
        'download_speed': download_speed_mbps,  # Send download speed in Mbps
        'server_monitoring_version': server_monitoring_version,
        'gui_version': gui_version,
        'current_time': current_time_str,  # The current time on the system
    }

def background_thread():
    """Background thread to periodically send data to clients"""
    while True:
        # Get system info
        system_info = get_system_info()

        # Send system info to all connected clients
        socketio.emit('update_system_info', system_info, broadcast=True)

        time.sleep(5)  # Wait 5 seconds between updates

@socketio.on('connect')
def handle_connect():
    """When a client connects, start the background thread"""
    socketio.start_background_task(background_thread)


@app.route('/')
def dashboard():
    return render_template('index.html')  # The main dashboard

@app.route('/processes')
def processes():
    num_cores = psutil.cpu_count(logical=True)  # Antal logiska kärnor
    process_data = []
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            cpu_percent = proc.cpu_percent(interval=0.1) / num_cores  # Dela CPU % med antal kärnor
            memory_percent = proc.memory_percent()

            process_info = {
                'pid': proc.pid,
                'name': proc.info['name'] if proc.info['name'] else "N/A",  # Hantera saknad processnamn
                'cpu_percent': f"{cpu_percent:.2f}",  # CPU % med två decimaler
                'memory_percent': f"{memory_percent:.2f}"  # Minnesanvändning i procent
            }
            process_data.append(process_info)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass  # Hantera processer som inte längre finns eller där åtkomst nekas

    return render_template('processes.html', processes=process_data)


@app.route('/kill_process/<int:pid>', methods=['POST'])
def kill_process(pid):
    try:
        proc = psutil.Process(pid)
        proc.terminate()  # Försök avsluta processen
        return redirect(url_for('processes'))  # Ladda om process-sidan efter avslutning
    except psutil.NoSuchProcess:
        return f"Process {pid} does not exist", 404
    except psutil.AccessDenied:
        return f"Permission denied to kill process {pid}", 403


@app.route('/logs')
def logs():
    return render_template('logs.html')  # Render log page

@app.route('/get_logs', methods=['GET'])
def get_logs():
    """Reads the log file and returns the content."""
    if os.path.exists(LOG_FILE_PATH):
        with open(LOG_FILE_PATH, 'r') as log_file:
            log_content = log_file.readlines()[-100:]  # Read the last 100 lines
            return jsonify(log_content)
    return jsonify({"error": "Log file not found."}), 404

@app.route('/get_log_summary', methods=['GET'])
def get_log_summary():
    """Provides a summary of log levels from the log file."""
    if os.path.exists(LOG_FILE_PATH):
        summary = {
            "info": 0,
            "warning": 0,
            "error": 0,
            "critical": 0
        }
        with open(LOG_FILE_PATH, 'r') as log_file:
            for line in log_file:
                if "INFO" in line:
                    summary["info"] += 1
                elif "WARNING" in line:
                    summary["warning"] += 1
                elif "ERROR" in line:
                    summary["error"] += 1
                elif "CRITICAL" in line:
                    summary["critical"] += 1
        return jsonify(summary)
    return jsonify({"error": "Log file not found."}), 404


@app.route('/network')
def network():
    return render_template('network.html')

@app.route('/disk')
def disk():
    disk_usage = psutil.disk_usage('/')
    return render_template('disk.html', disk_usage=disk_usage)

@app.route('/settings')
def settings():
    return render_template('settings.html')


