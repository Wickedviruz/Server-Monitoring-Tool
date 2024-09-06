import psutil
import time
import smtplib
from base.logger import log_message
from base.config import config, reload_config
from threading import Thread
import datetime
import socket
import platform
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Config parser and logging
enable_web_interface = config.getboolean('general', 'enable_web_interface')

# Parse threshold config
CPU_THRESHOLD = config.getint('thresholds', 'CPU_THRESHOLD')
MEMORY_THRESHOLD = config.getint('thresholds', 'MEMORY_THRESHOLD')
NETWORK_THRESHOLD = config.getint('thresholds', 'NETWORK_THRESHOLD')
DISK_THRESHOLD = config.getint('thresholds', 'DISK_THRESHOLD')

# Parse E-mail config
SENDER_EMAIL = config.get('email', 'SENDER_EMAIL')
RECEIVER_EMAILS = [email.strip() for email in config.get('email', 'RECEIVER_EMAILS').split(',')]
SMTP_SERVER = config.get('email', 'SMTP_SERVER')
SMTP_PORT = config.getint('email', 'SMTP_PORT')
SMTP_USER = config.get('email', 'SMTP_USER')
SMTP_PASSWORD = config.get('email', 'SMTP_PASSWORD')

os_type = platform.system()
hostname = socket.gethostname()

cpu_alert_sent = False
memory_alert_sent = False
network_alert_sent = False
disk_alert_sent = False
process_alert_sent = {}
last_report_time = datetime.datetime.now()

network_usage_samples = []
network_check_interval = 10
previous_sent = 0
previous_recv = 0
previous_time = time.time()

# Flask/SocketIO Server
def start_web_interface():
    if config.getboolean('general', 'enable_web_interface'):
        from GUI import app, socketio  # Import Flask GUI and SocketIO
        socketio.run(app, host='0.0.0.0', port=5000)

# Starta SocketIO-servern i en separat tråd
if enable_web_interface:
    flask_thread = Thread(target=start_web_interface)
    flask_thread.start()

# Skapa en funktion för att samla in och analysera nätverksdata
def monitor_network_usage():
    global previous_sent, previous_recv, previous_time

    # Hämta nuvarande nätverksstatistik
    net_info = psutil.net_io_counters()
    current_sent = net_info.bytes_sent
    current_recv = net_info.bytes_recv
    current_time = time.time()

    # Beräkna tidsskillnaden
    time_diff = current_time - previous_time

    sent_speed_mbit = 0
    recv_speed_mbit = 0

    if previous_sent != 0 and previous_recv != 0 and time_diff > 0:
        # Beräkna skillnaden i bytes skickade och mottagna
        sent_diff = current_sent - previous_sent
        recv_diff = current_recv - previous_recv

        # Omvandla till Mbit/s
        sent_speed_mbit = (sent_diff * 8) / (time_diff * 1_000_000)
        recv_speed_mbit = (recv_diff * 8) / (time_diff * 1_000_000)

        log_message("info", f"Sent: {sent_speed_mbit:.2f} Mbit/s, Received: {recv_speed_mbit:.2f} Mbit/s")

        # Kontrollera om trafiken överskrider tröskelvärdet (i Mbit/s)
        if sent_speed_mbit > NETWORK_THRESHOLD or recv_speed_mbit > NETWORK_THRESHOLD:
            log_message("warning", f"High network traffic detected. Sent: {sent_speed_mbit:.2f} Mbit/s, Received: {recv_speed_mbit:.2f} Mbit/s")
            send_email(
                subject="Warning: High network traffic",
                body=f"High network traffic detected. Sent: {sent_speed_mbit:.2f} Mbit/s, Received: {recv_speed_mbit:.2f} Mbit/s"
            )

    # Uppdatera föregående värden för nästa mätning
    previous_sent = current_sent
    previous_recv = current_recv
    previous_time = current_time

    # Returnera nätverkshastigheter
    return sent_speed_mbit, recv_speed_mbit


def detect_ddos_pattern():
    global previous_sent, previous_recv

    if previous_sent != 0 and previous_recv != 0:
        sent_diff = previous_sent
        recv_diff = previous_recv

        # Om hastigheten har ökat drastiskt över ett par mätningar
        if sent_diff > NETWORK_THRESHOLD or recv_diff > NETWORK_THRESHOLD:
            log_message("warning", "DDoS pattern detected.")
            send_email(
                subject="Critical Warning: DDoS Attack Pattern Detected",
                body="Multiple network traffic spikes detected, which may indicate a DDoS attack."
            )
            previous_sent = 0  # Nollställ för att undvika fler varningar för samma händelse
            previous_recv = 0

def send_email(subject, body):
    subject = f"{hostname} - {subject}"
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = ', '.join(RECEIVER_EMAILS)
    msg['Subject'] = subject

    body = f"Server: {hostname}\n\n{body}"
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        text = msg.as_string()
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAILS, text)
        server.quit()
        log_message("info", "Email sent!")
    except Exception as e:
        log_message("error", f"Failed to send email. Error: {e}")



def restart_process(process_name):
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] == process_name:
            os.kill(proc.info['pid'], 9)
            log_message("info", f"{process_name} was killed due to high resource usage.")
            os.system(f"systemctl restart {process_name}")
            log_message("info", f"{process_name} was restarted.")

def monitor_process(process_name, cpu_threshold, memory_threshold, restart_on_failure):
    global process_alert_sent
    process_found = False
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        if proc.info['name'] == process_name:
            process_found = True
            if proc.info['cpu_percent'] > cpu_threshold or proc.info['memory_percent'] > memory_threshold:
                if process_name not in process_alert_sent or not process_alert_sent[process_name]:
                    log_message("warning", f"{process_name} is using high resources")
                    send_email(
                        subject=f"Warning: High resource usage by {process_name}",
                        body=f"{process_name} is using {proc.info['cpu_percent']}% CPU and {proc.info['memory_percent']}% memory."
                    )
                    process_alert_sent[process_name] = True
            else:
                process_alert_sent[process_name] = False
            break

    if not process_found and restart_on_failure:
        log_message("error", f"{process_name} is not running, attempting to restart.")
        restart_process(process_name)

def monitor_disk_partitions():
    for part in psutil.disk_partitions():
        usage = psutil.disk_usage(part.mountpoint)
        if usage.percent > DISK_THRESHOLD:
            log_message("warning", f"High disk usage on {part.device}: {usage.percent}%")
            send_email(
                subject="Warning: High disk usage",
                body=f"Disk usage on {part.device} is at {usage.percent}%, exceeding the threshold {DISK_THRESHOLD}%."
            )

if os_type == "Linux":
    log_message("info", "Running on Linux")
elif os_type == "Windows":
    log_message("info", "Running on Windows")
else:
    log_message("warning", f"Unsupported OS: {os_type}")

log_message("info", "Monitoring started")
while True:
    # Gets current time for status check
    current_time = datetime.datetime.now()

    # Check CPU-usage
    cpu_usage = psutil.cpu_percent(interval=1)

    # Check memory usage
    memory_info = psutil.virtual_memory()
    memory_usage = memory_info.percent

    # Check network usage
    sent_speed, recv_speed = monitor_network_usage()
    detect_ddos_pattern()

    # Check disk usage
    disk_info = psutil.disk_usage('/')
    disk_usage = disk_info.percent

    if cpu_usage > CPU_THRESHOLD:
        if not cpu_alert_sent:
            log_message("warning", "CPU usage is high")
            send_email(
                subject="Warning: High CPU-usage",
                body=f"CPU-usage is currently {cpu_usage}%, which is higher than the threshold {CPU_THRESHOLD}%."
            )
            cpu_alert_sent = True
    else:
        cpu_alert_sent = False

    if memory_usage > MEMORY_THRESHOLD:
        if not memory_alert_sent:
            log_message("warning", "Memory usage is high")
            send_email(
                subject="Warning: High memory usage",
                body=f"Memory usage is currently {memory_usage}%, which is higher than the threshold {MEMORY_THRESHOLD}%."
            )
            memory_alert_sent = True
    else:
        memory_alert_sent = False

    if sent_speed > NETWORK_THRESHOLD or recv_speed > NETWORK_THRESHOLD:
        if not network_alert_sent:
            log_message("warning", "Network usage is high")
            send_email(
                subject="Warning: High network traffic",
                body=f"Network traffic has exceeded the threshold. Upload: {sent_speed:.2f} Mbps, Download: {recv_speed:.2f} Mbps."
            )
            network_alert_sent = True
    else:
        network_alert_sent = False

    for section in config.sections():
        if section.startswith("process"):
            process_name = config.get(section, "process_name")
            cpu_threshold = config.getint(section, "cpu_threshold")
            memory_threshold = config.getint(section, "memory_threshold")
            restart_on_failure = config.getboolean(section, "restart_on_failure")
            monitor_process(process_name, cpu_threshold, memory_threshold, restart_on_failure)

    if (current_time - last_report_time).total_seconds() > 86400:
        send_email(
            subject=f"Server Status: All OK on {hostname}",
            body=f"Server: {hostname}\n\nAll systems are operational. No issues detected in the last 24 hours."
        )
        last_report_time = current_time

    time.sleep(network_check_interval)