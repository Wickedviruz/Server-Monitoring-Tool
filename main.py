import eventlet
from threading import Thread
from GUI import app, socketio
from utils.system_monitor import monitor_cpu, monitor_memory, monitor_disk_partitions, monitor_network_usage, detect_ddos_pattern, get_operatingsystem
from utils.process_monitor import monitor_process
from utils.logger import log_message
from utils.mailer import send_email
from utils.config import config
import socket
import datetime
import time

eventlet.monkey_patch()  # Lägg till detta för att använda eventlet

hostname = socket.gethostname()

# Main monitoring loop
def monitor_resources():
    global last_report_time
    last_report_time = datetime.datetime.now()
    while True:
        current_time = datetime.datetime.now()

        # CPU, Memory, Network, and Disk alerts
        monitor_cpu()
        monitor_memory()
        monitor_network_usage()
        detect_ddos_pattern()
        monitor_disk_partitions()
        get_operatingsystem()
        

        # Monitor Processes
        for section in config.sections():
            if section.startswith("process"):
                process_name = config.get(section, "process_name")
                cpu_threshold = config.getint(section, "cpu_threshold")
                memory_threshold = config.getint(section, "memory_threshold")
                restart_on_failure = config.getboolean(section, "restart_on_failure")
                monitor_process(process_name, cpu_threshold, memory_threshold, restart_on_failure)

        # Send daily report
        if (current_time - last_report_time).total_seconds() > 86400:
            send_email(
                subject=f"Server Status: All OK on {hostname}",
                body=f"Server: {hostname}\n\nAll systems are operational. No issues detected in the last 24 hours."
            )
            last_report_time = current_time

        time.sleep(10)

if __name__ == '__main__':
    # Start resource monitoring in a separate thread
    monitoring_thread = Thread(target=monitor_resources)
    monitoring_thread.start()

    # Kontrollera config och starta Flask/SocketIO om WEB_GUI är aktiverat
    if config.getboolean('general', 'WEB_GUI'):
        log_message("info","Starting Flask/SocketIO server with eventlet...")
        socketio.run(app, host='0.0.0.0', port=5000, debug=True, use_reloader=False)
