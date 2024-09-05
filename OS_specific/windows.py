import os
from base.logger import log_message

def manage_service(service_name, action):
    os.system(f"net {action} {service_name}")
    log_message("info", f"Service {service_name} {action}ed on Windows.")

def add_user(username):
    os.system(f"net user {username} /add")
    log_message("info", f"User {username} added on Windows.")

def restart_process_windows(process_name):
    """Specifik metod för att starta om processer i Windows"""
    os.system(f"taskkill /F /IM {process_name}")
