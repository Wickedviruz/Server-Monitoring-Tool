# GUI/routes.py
from GUI import app
from flask import render_template
from flask_socketio import SocketIO, emit
import psutil
import socket
import time

hostname = socket.gethostname()
socketio = SocketIO(app)

# Variabler för att hålla tidigare nätverksdata
last_net_io = psutil.net_io_counters()
last_time = time.time()

@app.route('/')
def index():
    return render_template('index.html', hostname=hostname)

@socketio.on('request_data')
def handle_request_data():
    global last_net_io, last_time
    while True:
        cpu_usage = psutil.cpu_percent(interval=1)
        memory_info = psutil.virtual_memory()
        memory_usage = memory_info.percent
        disk_info = psutil.disk_usage('/')
        disk_usage = disk_info.percent

        # Hämta aktuellt nätverksdata
        net_io = psutil.net_io_counters()
        current_time = time.time()

        # Beräkna nätverkshastighet (bytes per sekund)
        bytes_sent_per_sec = (net_io.bytes_sent - last_net_io.bytes_sent) / (current_time - last_time)
        bytes_recv_per_sec = (net_io.bytes_recv - last_net_io.bytes_recv) / (current_time - last_time)

        # Konvertera till megabits per sekund (Mbps)
        upload_speed_mbps = (bytes_sent_per_sec * 8) / (1024 * 1024)
        download_speed_mbps = (bytes_recv_per_sec * 8) / (1024 * 1024)

        # Spara nuvarande nätverksdata för nästa beräkning
        last_net_io = net_io
        last_time = current_time

        # Skicka data till klienten
        emit('update_data', {
            'cpu_usage': cpu_usage,
            'memory_usage': memory_usage,
            'disk_usage': disk_usage,
            'upload_speed': round(upload_speed_mbps, 2),
            'download_speed': round(download_speed_mbps, 2)
        })

        time.sleep(5)  # Vänta 5 sekunder mellan uppdateringar

