import os
from base.logger import log_message

def manage_service(service_name, action):
    os.system(f"systemctl {action} {service_name}")
    log_message("info", f"Service {service_name} {action}ed on Linux.")

def add_user(username):
    os.system(f"useradd {username}")
    log_message("info", f"User {username} added on Linux.")

def restart_process_linux(process_name):
    """Specifik metod för att starta om processer i Linux"""
    os.system(f"systemctl restart {process_name}")
