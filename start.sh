#!/bin/bash

# Activate virtual environment (adjust the path as needed)
source /home/ec2-user/venv/bin/activate

# Ensure a logs directory exists
LOG_DIR="/home/ec2-user/Stock-Scanner-Project/logs"
mkdir -p "$LOG_DIR"

# Declare non-email Flask apps and their ports
declare -A apps=(
    ["DVSA.50_DVSA_flask"]=5001
    ["DVSA.100_DVSA_flask"]=5002
    ["DVSA.150_DVSA_flask"]=5003
    ["MC_Change.10_mc_de_flask"]=5004
    ["MC_Change.10_mc_in_flask"]=5005
    ["MC_Change.20_mc_de_flask"]=5006
    ["MC_Change.20_mc_in_flask"]=5007
    ["MC_Change.30_mc_de_flask"]=5008
    ["MC_Change.30_mc_in_flask"]=5009
    ["PE_Change.10_pe_de_flask"]=5010
    ["PE_Change.10_pe_in_flask"]=5011
    ["PE_Change.20_pe_de_flask"]=5012
    ["PE_Change.20_pe_in_flask"]=5013
    ["PE_Change.30_pe_de_flask"]=5014
    ["PE_Change.30_pe_in_flask"]=5015
    ["Price_de.10_price_de_flask"]=5016
    ["Price_de.15_Price_de_flask"]=5017
    ["Price_de.20_price_de_flask"]=5018
    ["Price_in.20_price_in_flask"]=5019
    ["Price_in.50_price_in_flask"]=5020
    ["Price_in.75_price_in_flask"]=5021
    ["Volume.1.125_volume_flask"]=5022
    ["Volume.1.25_volume_flask"]=5023
    ["Volume.1.5_volume_flask"]=5024
    ["Volume.1.75_volume_flask"]=5025
    ["Volume.2_volume_flask"]=5026
    ["Volume.2.5_volume_flask"]=5027
    ["Volume.3_volume_flask"]=5028
    ["Volume.5x_volume_flask"]=5029
)

# Declare email-related scripts (including Email_filter.py)
declare -a email_apps=(
    "DVSA/50_DVSA_email.py"
    "DVSA/100_DVSA_email.py"
    "DVSA/150_DVSA_email.py"
    "MC_Change/10_mc_de_email.py"
    "MC_Change/10_mc_in_email.py"
    "MC_Change/20_mc_de_email.py"
    "MC_Change/20_mc_in_email.py"
    "MC_Change/30_mc_de_email.py"
    "MC_Change/30_mc_in_email.py"
    "PE_Change/10_pe_de_email.py"
    "PE_Change/10_pe_in_email.py"
    "PE_Change/20_pe_de_email.py"
    "PE_Change/20_pe_in_email.py"
    "PE_Change/30_pe_de_email.py"
    "PE_Change/30_pe_in_email.py"
    "Price_de/10_price_de_email.py"
    "Price_de/15_Price_de_email.py"
    "Price_de/20_price_de_email.py"
    "Price_in/20_price_in_email.py"
    "Price_in/50_price_in_email.py"
    "Price_in/75_price_in_email.py"
    "Volume/1.125_volume_email.py"
    "Volume/1.25_volume_email.py"
    "Volume/1.5_volume_email.py"
    "Volume/1.75_volume_email.py"
    "Volume/2_volume_email.py"
    "Volume/2.5_volume_email.py"
    "Volume/3_volume_email.py"
    "Volume/5_volume_email.py"
    "Email_filter.py"
)

# Start all non-email Flask apps using gunicorn
for app in "${!apps[@]}"; do
    port=${apps[$app]}
    nohup gunicorn --chdir "blueprint" "$app:app" --bind "0.0.0.0:$port" > "$LOG_DIR/${app//./_}.log" 2>&1 &
done

# Function to manage email scripts based on New York time
manage_email_scripts() {
    # Get the current hour in New York (using 24-hour format)
    current_hour=$(TZ="America/New_York" date +%H)
    
    # Determine if it's within the allowed window:
    # Allowed if current hour is >= 8 OR < 5.
    # (Assuming a period from 8:00 to 05:00 the next day.)
    if (( 10#$current_hour >= 8 || 10#$current_hour < 5 )); then
        # Start or ensure email scripts are running
        for script in "${email_apps[@]}"; do
            script_name=$(basename "$script")
            app_name="${script_name%.py}"
            # Check if already running; if not, start it.
            if ! pgrep -f "$script" > /dev/null; then
                nohup python "$script" > "$LOG_DIR/${script_name}.log" 2>&1 &
                echo "Started $script (email group)"
            fi
        done
    else
        # Outside allowed window; kill email scripts if running
        for script in "${email_apps[@]}"; do
            pkill -f "$script"
            echo "Stopped $script (email group) because it's outside allowed time."
        done
    fi
}

# Run email script manager every minute in the background
while true; do
    manage_email_scripts
    sleep 60
done