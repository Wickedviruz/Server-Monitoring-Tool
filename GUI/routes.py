# GUI/routes.py
from GUI import app
from flask import render_template
import psutil
import socket

hostname = socket.gethostname()

@app.route('/')
def index():
    cpu_usage = psutil.cpu_percent(interval=1)
    memory_info = psutil.virtual_memory()
    memory_usage = memory_info.percent
    disk_info = psutil.disk_usage('/')
    disk_usage = disk_info.percent
    return render_template('index.html', 
                            hostname=hostname, 
                            cpu_usage=cpu_usage, 
                            memory_usage=memory_usage,
                            disk_usage=disk_usage)
