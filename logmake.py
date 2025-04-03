import os

# Project directory
PROJECT_DIR = "/home/ec2-user/Stock-Scanner-Project"
LOG_DIR = os.path.join(PROJECT_DIR, "logs")

# Ensure logs directory exists
os.makedirs(LOG_DIR, exist_ok=True)

# List of email scripts (including the Email filter)
EMAIL_SCRIPTS = [
    "50_DVSA_email.py",
    "100_DVSA_email.py",
    "150_DVSA_email.py",
    "10_mc_de_email.py",
    "10_mc_in_email.py",
    "20_mc_de_email.py",
    "20_mc_in_email.py",
    "30_mc_de_email.py",
    "30_mc_in_email.py",
    "10_pe_de_email.py",
    "10_pe_in_email.py",
    "20_pe_de_email.py",
    "20_pe_in_email.py",
    "30_pe_de_email.py",
    "30_pe_in_email.py",
    "10_price_de_email.py",
    "15_Price_de_email.py",
    "20_price_de_email.py",
    "20_price_in_email.py",
    "50_price_in_email.py",
    "75_price_in_email.py",
    "1.125_volume_email.py",
    "1.25_volume_email.py",
    "1.5_volume_email.py",
    "1.75_volume_email.py",
    "2_volume_email.py",
    "2.5_volume_email.py",
    "3_volume_email.py",
    "5_volume_email.py",
    "Email_filter.py"
]

def create_log_files():
    """Create log files for each script in EMAIL_SCRIPTS"""
    for script in EMAIL_SCRIPTS:
        log_file = os.path.join(LOG_DIR, f"{script}.log")
        
        # Ensure the log file exists
        open(log_file, "a").close()
        print(f"Log file created: {log_file}")

if __name__ == "__main__":
    create_log_files()
    print("All log files created.")
    
