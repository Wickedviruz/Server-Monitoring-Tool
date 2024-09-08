# process monitor.py
# Externa libs import
import psutil
import os

# Local module imports
from utils.logger import log_message
from utils.mailer import send_alert

process_alert_sent = {}

# Process Monitoring
def monitor_process(process_name, cpu_threshold, memory_threshold, restart_on_failure):
    global process_alert_sent
    process_found = False
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        if proc.info['name'] == process_name:
            process_found = True
            if proc.info['cpu_percent'] > cpu_threshold or proc.info['memory_percent'] > memory_threshold:
                if process_name not in process_alert_sent or not process_alert_sent[process_name]:
                    send_alert(f"Process {process_name}", f"High resource usage: {proc.info['cpu_percent']}% CPU, {proc.info['memory_percent']}% Memory")
                    process_alert_sent[process_name] = True
            else:
                process_alert_sent[process_name] = False
            break

    if not process_found and restart_on_failure:
        send_alert(f"Process {process_name}", "Process not found, attempting to restart.")
        restart_process(process_name)

def restart_process(process_name):
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] == process_name:
            os.kill(proc.info['pid'], 9)
            log_message("info", f"{process_name} was killed due to high resource usage.")
            os.system(f"systemctl restart {process_name}")
            log_message("info", f"{process_name} was restarted.")
