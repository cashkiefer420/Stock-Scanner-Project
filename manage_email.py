import os
import time
import subprocess
from datetime import datetime
import pytz

# Project directory
PROJECT_DIR = "/home/ec2-user/Stock-Scanner-Project"
LOG_DIR = os.path.join(PROJECT_DIR, "logs")

# Ensure logs directory exists
os.makedirs(LOG_DIR, exist_ok=True)

# List of email scripts (including the Email filter)
EMAIL_SCRIPTS = [
    "DVSA.50_DVSA_email",
    "DVSA.100_DVSA_email",
    "DVSA.150_DVSA_email",
    "MC_Change.10_mc_de_email",
    "MC_Change.10_mc_in_email",
    "MC_Change.20_mc_de_email",
    "MC_Change.20_mc_in_email",
    "MC_Change.30_mc_de_email",
    "MC_Change.30_mc_in_email",
    "PE_Change.10_pe_de_email",
    "PE_Change.10_pe_in_email",
    "PE_Change.20_pe_de_email",
    "PE_Change.20_pe_in_email",
    "PE_Change.30_pe_de_email",
    "PE_Change.30_pe_in_email",
    "Price_de.10_price_de_email",
    "Price_de.15_Price_de_email",
    "Price_de.20_price_de_email",
    "Price_in.20_price_in_email",
    "Price_in.50_price_in_email",
    "Price_in.75_price_in_email",
    "Volume.1.125_volume_email",
    "Volume.1.25_volume_email",
    "Volume.1.5_volume_email",
    "Volume.1.75_volume_email",
    "Volume.2_volume_email",
    "Volume.2.5_volume_email",
    "Volume.3_volume_email",
    "Volume.5_volume_email",
    "Email_filter"
]

# Get New York timezone
NY_TZ = pytz.timezone("America/New_York")


def is_within_allowed_time():
    """Returns True if the current time in New York is between 8 AM - 5 AM"""
    ny_time = datetime.now(NY_TZ)
    hour = ny_time.hour
    return hour >= 8 or hour < 5


def start_email_scripts():
    """Start email scripts that are not running"""
    for script in EMAIL_SCRIPTS:
        log_file = os.path.join(LOG_DIR, f"{script}.log")

        # Check if the script is already running
        if not is_script_running(script):
            script_path = os.path.join(PROJECT_DIR, script.replace(".", "/") + ".py")
            if os.path.exists(script_path):
                with open(log_file, "a") as log:
                    subprocess.Popen(["python", script_path], stdout=log, stderr=log)
                print(f"Started {script_path}")
            else:
                print(f"Error: {script_path} not found!")


def stop_email_scripts():
    """Stop all running email scripts"""
    for script in EMAIL_SCRIPTS:
        script_name = script.replace(".", "/") + ".py"
        os.system(f"pkill -f {script_name}")
        print(f"Stopped {script_name}")


def is_script_running(script):
    """Check if a script is running"""
    script_name = script.replace(".", "/") + ".py"
    try:
        output = subprocess.check_output(f"pgrep -f {script_name}", shell=True).decode().strip()
        return bool(output)
    except subprocess.CalledProcessError:
        return False


def manage_email_scripts():
    """Main loop to start/stop scripts based on allowed time"""
    while True:
        if is_within_allowed_time():
            start_email_scripts()
        else:
            stop_email_scripts()
        time.sleep(60)  # Check every minute


if __name__ == "__main__":
    manage_email_scripts()
