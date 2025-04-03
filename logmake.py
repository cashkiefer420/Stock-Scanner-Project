import os

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

def create_log_files():
    """Create log files for each script in EMAIL_SCRIPTS"""
    for script in EMAIL_SCRIPTS:
        script_name = script.replace(".", "/") + ".py"
        log_file = os.path.join(LOG_DIR, f"{script_name}.log")

        # Ensure the log file exists
        open(log_file, "a").close()
        print(f"Log file created: {log_file}")

if __name__ == "__main__":
    create_log_files()
    print("All log files created.")
