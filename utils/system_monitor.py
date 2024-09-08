import psutil
import time
import platform
from utils.logger import log_message
from utils.mailer import send_alert
from utils.config import config

# Global variables
previous_sent = 0
previous_recv = 0
previous_time = time.time()
os_type = platform.system()

CPU_THRESHOLD = config.getint('thresholds', 'CPU_THRESHOLD')
MEMORY_THRESHOLD = config.getint('thresholds', 'MEMORY_THRESHOLD')
NETWORK_THRESHOLD = config.getint('thresholds', 'NETWORK_THRESHOLD')
DISK_THRESHOLD = config.getint('thresholds', 'DISK_THRESHOLD')

cpu_alert_sent = False
memory_alert_sent = False
network_alert_sent = False
disk_alert_sent = False

# CPU Monitoring
def monitor_cpu():
    global cpu_alert_sent
    cpu_usage = psutil.cpu_percent(interval=1)
    if cpu_usage > CPU_THRESHOLD:
        if not cpu_alert_sent:
            send_alert("CPU", f"CPU usage is at {cpu_usage}%")
            cpu_alert_sent = True
    else:
        cpu_alert_sent = False

# Memory Monitoring
def monitor_memory():
    global memory_alert_sent
    memory_info = psutil.virtual_memory()
    memory_usage = memory_info.percent
    if memory_usage > MEMORY_THRESHOLD:
        if not memory_alert_sent:
            send_alert("Memory", f"Memory usage is at {memory_usage}%")
            memory_alert_sent = True
    else:
        memory_alert_sent = False

# Disk Monitoring
def monitor_disk_partitions():
    global disk_alert_sent
    for part in psutil.disk_partitions():
        usage = psutil.disk_usage(part.mountpoint)
        if usage.percent > DISK_THRESHOLD:
            if not disk_alert_sent:
                send_alert("Disk", f"Disk usage on {part.device} is at {usage.percent}%")
                disk_alert_sent = True
        else:
            disk_alert_sent = False

# Network Monitoring
def monitor_network_usage():
    global previous_sent, previous_recv, previous_time
    net_info = psutil.net_io_counters()
    current_sent = net_info.bytes_sent
    current_recv = net_info.bytes_recv
    current_time = time.time()

    time_diff = current_time - previous_time
    sent_speed_mbit = 0
    recv_speed_mbit = 0

    if previous_sent != 0 and previous_recv != 0 and time_diff > 0:
        sent_diff = current_sent - previous_sent
        recv_diff = current_recv - previous_recv

        sent_speed_mbit = (sent_diff * 8) / (time_diff * 1_000_000)
        recv_speed_mbit = (recv_diff * 8) / (time_diff * 1_000_000)


        if sent_speed_mbit > NETWORK_THRESHOLD or recv_speed_mbit > NETWORK_THRESHOLD:
            log_message("info", f"Sent: {sent_speed_mbit:.2f} Mbit/s, Received: {recv_speed_mbit:.2f} Mbit/s")
            send_alert("Network", f"High network traffic: Sent {sent_speed_mbit:.2f} Mbit/s, Received {recv_speed_mbit:.2f} Mbit/s")

    previous_sent = current_sent
    previous_recv = current_recv
    previous_time = current_time

    return sent_speed_mbit, recv_speed_mbit

# Detect DDoS pattern
def detect_ddos_pattern():
    sent_speed_mbit, recv_speed_mbit = monitor_network_usage()
    if sent_speed_mbit > NETWORK_THRESHOLD or recv_speed_mbit > NETWORK_THRESHOLD:
        send_alert("Network", "DDoS pattern detected.")


def get_operatingsystem():
    if os_type == "Linux":
        log_message("info", "Running on Linux")
    elif os_type == "Windows":
        log_message("info", "Running on Windows")
    else:
        log_message("warning", f"Unsupported OS: {os_type}")