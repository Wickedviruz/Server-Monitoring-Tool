# Server Monitoring Tool

![Server Monitoring](https://img.shields.io/badge/Server-Monitoring-green.svg)

## Overview

The Server Monitoring Tool is a lightweight and powerful Python-based monitoring solution designed to keep track of key server metrics such as CPU usage, memory usage, disk usage, network traffic, and processes. It can send alerts via email when defined thresholds are exceeded, and it supports both Linux and Windows environments. Additionally, a simple web-based interface can be enabled to monitor metrics in real-time.

## Features

- **CPU, Memory, and Disk Usage Monitoring**: Track resource usage and receive alerts when usage exceeds defined thresholds.
- **Network Traffic Monitoring**: Monitor network activity and detect potential DDoS attacks.
- **Process Monitoring**: Ensure critical processes are running and within resource limits. Automatically restart processes if they crash or exceed thresholds.
- **Email Notifications**: Receive real-time alerts via email when thresholds are exceeded.
- **Web Interface (Optional)**: Enable a simple web-based interface to monitor metrics in real-time.
- **Cross-Platform Support**: Works on both Linux and Windows servers.

## Installation

1. **Clone the repository:**

    ```bash
    git clone https://github.com/yourusername/server-monitoring-tool.git
    cd server-monitoring-tool
    ```

2. **Create and activate a virtual environment (optional but recommended):**

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. **Install the required Python packages:**

    ```bash
    pip install -r requirements.txt
    ```

4. **Set up the configuration file:**

    - Copy the example configuration file:

    ```bash
    cp config.example.ini config.ini
    ```

    - Edit the `config.ini` file with your specific settings:

    ```ini
    [email]
    SENDER_EMAIL = "your_email@example.com"
    RECEIVER_EMAIL = "receiver_email@example.com"
    SMTP_SERVER = "smtp.example.com"
    SMTP_PORT = 587
    SMTP_USER = "your_smtp_user"
    SMTP_PASSWORD = "your_smtp_password"

    [thresholds]
    CPU_THRESHOLD = 80
    MEMORY_THRESHOLD = 80
    NETWORK_THRESHOLD = 1000000000
    DISK_THRESHOLD = 90
    ```

## Usage

Run the monitoring script:

```bash
python watch.py


The script will start monitoring the server based on the configured thresholds and send email notifications when necessary. If the web interface is enabled in the configuration, it will also start the Flask web server.

## Configuration

### General Settings

- **enable_web_interface**: Set to `true` to enable the web interface.

### Email Settings

- **SENDER_EMAIL**: The email address from which notifications will be sent.
- **RECEIVER_EMAIL**: The email address(es) to receive notifications (comma-separated for multiple).
- **SMTP_SERVER**: The SMTP server to use for sending emails.
- **SMTP_PORT**: The port to use for the SMTP server (usually 587 for TLS).
- **SMTP_USER**: The SMTP username.
- **SMTP_PASSWORD**: The SMTP password.

### Thresholds

- **CPU_THRESHOLD**: The CPU usage percentage threshold for alerts.
- **MEMORY_THRESHOLD**: The memory usage percentage threshold for alerts.
- **NETWORK_THRESHOLD**: The network usage threshold (in bytes) for alerts.
- **DISK_THRESHOLD**: The disk usage percentage threshold for alerts.

### Process Monitoring

Add sections for specific processes you want to monitor:

```ini
[process:example_process]
process_name = "example_process_name"
cpu_threshold = 50
memory_threshold = 50
restart_on_failure = true


## Contributing

Contributions are welcome! Please fork this repository and submit a pull request with your changes. For major changes, please open an issue first to discuss what you would like to change.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## Acknowledgements

- [psutil](https://github.com/giampaolo/psutil) for system monitoring capabilities.
- [Flask](https://flask.palletsprojects.com/) for the optional web interface.
