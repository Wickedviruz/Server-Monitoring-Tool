from base.config import config
from base.logger import log_message
from threading import Thread
from GUI import app as gui_app
import platform
import Watch

def start_web_interface():
    """Startar Flask webben om aktiverad"""
    if config.getboolean('general', 'enable_web_interface'):
        flask_thread = Thread(target=gui_app.run, kwargs={'host': '0.0.0.0', 'port': 5000})
        flask_thread.start()
        log_message("info", "Web interface started")

def main():
    """Startar övervakningsskript och webben"""
    os_type = platform.system()
    log_message("info", f"Running on {os_type}")

    start_web_interface()
    
    # Starta övervakningen
    Watch()

if __name__ == '__main__':
    main()
