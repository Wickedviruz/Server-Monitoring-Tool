import psutil
import time
import smtplib
import logging
import datetime
import configparser
import socket
import platform
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart



# Config parser and logging
config = configparser.ConfigParser()
config.read('config.ini')
logging.basicConfig(filename='server_monitor.log', level=logging.INFO,
                    format='%(asctime)s %(levelname)s: %(message)s')

# Parse general config
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

os_type =platform.system()


# Prevents from spamming emails
cpu_alert_sent = False
memory_alert_sent = False
network_alert_sent = False
disk_alert_sent = False
process_alert_sent = {}
last_report_time = datetime.datetime.now()
hostname = socket.gethostname()

# Nätverkstrafik övervakning under en viss tidsperiod
network_usage_samples = []
network_check_interval = 10  # sekunder mellan varje nätverkskontroll
network_monitor_duration = 60  # total period för att samla in nätverksdata

# Import Flask GUI
if config.getboolean('general', 'enable_web_interface'):
    from GUI import app
    from threading import Thread

if enable_web_interface:
    # Starta Flask-applikationen i en separat tråd så att den inte blockerar övervakningsloopen
    flask_thread = Thread(target=app.run, kwargs={'host': '0.0.0.0', 'port': 5000})
    flask_thread.start()

def log_message(level, message):
    message = f"{hostname}: {message}"
    if level == "info":
        logging.info(message)
    elif level == "warning":
        logging.warning(message)
    elif level == "error":
        logging.error(message)

def reload_config():
    config.read('config.ini')
    log_message("info", "Configuration reloaded")

# Skapa en funktion för att samla in och analysera nätverksdata
def monitor_network_usage():
    global network_usage_samples
    net_info = psutil.net_io_counters()
    bytes_sent = net_info.bytes_sent
    bytes_recv = net_info.bytes_recv

    # Spara den senaste nätverksstatistiken
    network_usage_samples.append((bytes_sent, bytes_recv))

    # Om vi har samlat tillräckligt med data, analysera den
    if len(network_usage_samples) * network_check_interval >= network_monitor_duration:
        initial_sent, initial_recv = network_usage_samples[0]
        final_sent, final_recv = network_usage_samples[-1]

        # Beräkna skillnaden i bytes
        sent_diff = final_sent - initial_sent
        recv_diff = final_recv - initial_recv

        # Kontrollera om det finns en dramatisk ökning i trafiken
        if sent_diff > NETWORK_THRESHOLD or recv_diff > NETWORK_THRESHOLD:
            log_message("warning", "Sudden increase in network traffic detected.")
            send_email(
                subject="Warning: Potential DDoS Attack Detected",
                body=f"Significant network traffic detected over the last {network_monitor_duration} seconds. "
                     f"Bytes received: {recv_diff}, Bytes sent: {sent_diff}."
            )

        network_usage_samples = []
    
    log_message("info", "Collecting network data for analysis")

    #Return the latest values
    return bytes_recv, bytes_sent

def detect_ddos_pattern():
    if len(network_usage_samples) >= 3:  # Vi behöver åtminstone 3 dataloggningar för att analysera trender
        sent_diffs = [network_usage_samples[i+1][0] - network_usage_samples[i][0] for i in range(len(network_usage_samples)-1)]
        recv_diffs = [network_usage_samples[i+1][1] - network_usage_samples[i][1] for i in range(len(network_usage_samples)-1)]

        # Kolla om trafiken ökar snabbt
        if all(diff > NETWORK_THRESHOLD for diff in sent_diffs) or all(diff > NETWORK_THRESHOLD for diff in recv_diffs):
            log_message("warning", "DDoS pattern detected.")
            send_email(
                subject="Critical Warning: DDoS Attack Pattern Detected",
                body="Multiple network traffic spikes detected, which may indicate a DDoS attack."
            )
            # Tömma samples för att undvika fler varningar för samma händelse
            network_usage_samples.clear()

def send_email(subject, body):
    for email in RECEIVER_EMAILS:
        subject = f"{hostname} - {subject}"
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECEIVER_EMAILS
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
    bytes_recv, bytes_sent = monitor_network_usage()
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

    if (bytes_recv > NETWORK_THRESHOLD or bytes_sent > NETWORK_THRESHOLD):
        if not network_alert_sent:
            log_message("warning", "Network usage is high")
            send_email(
                subject="Warning: High network traffic",
                body=f"Network traffic has exceeded the threshold. Bytes received: {bytes_recv}, Bytes sent: {bytes_sent}."
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