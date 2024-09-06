import configparser
import os
from base.logger import log_message

config = configparser.ConfigParser()

# Hitta den absoluta sökvägen till config.ini
config_file = os.path.join(os.path.dirname(__file__), '..', 'config.ini')

# Läs konfigurationsfilen
config.read(config_file)

def reload_config():
    config.read(config_file)
    log_message("info", "Configuration reloaded")
