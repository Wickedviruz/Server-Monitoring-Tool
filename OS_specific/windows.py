import os
from utils.logging import log_message

def manage_service(service_name, action):
    os.system(f"net {action} {service_name}")
    log_message("info", f"Service {service_name} {action}ed on Windows.")

def add_user(username):
    os.system(f"net user {username} /add")
    log_message("info", f"User {username} added on Windows.")
