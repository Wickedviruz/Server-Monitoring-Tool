import logging
import socket

hostname = socket.gethostname()

logging.basicConfig(filename='server_monitor.log', level=logging.INFO,
                    format='%(asctime)s %(levelname)s: %(message)s')

def log_message(level, message):
    message = f"{hostname}: {message}"
    if level == "info":
        logging.info(message)
    elif level == "warning":
        logging.warning(message)
    elif level == "error":
        logging.error(message)
    elif level == "critical":
        logging.critical(message)
