import configparser
import os
from utils.logger import log_message

config = configparser.ConfigParser()

# Absolute filepath for  config.ini
config_file = os.path.join(os.path.dirname(__file__), '..', 'config.ini')

# read the config file
config.read(config_file)

def reload_config():
    config.read(config_file)
    log_message("info", "Configuration reloaded")
