#!/bin/bash

# Activate virtual environment (adjust the path as needed)
source /home/ec2-user/venv/bin/activate

# Ensure a logs directory exists
LOG_DIR="/home/ec2-user/Stock-Scanner-Project/logs"
mkdir -p "$LOG_DIR"

# Declare Flask apps and their ports (updated to treat as files)
declare -A apps=(
    ["DVSA/50_DVSA_flask.py"]=5001
    ["DVSA/100_DVSA_flask.py"]=5002
    ["DVSA/150_DVSA_flask.py"]=5003
    ["MC_Change/10_mc_de_flask.py"]=5004
    ["MC_Change/10_mc_in_flask.py"]=5005
    ["MC_Change/20_mc_de_flask.py"]=5006
    ["MC_Change/20_mc_in_flask.py"]=5007
    ["MC_Change/30_mc_de_flask.py"]=5008
    ["MC_Change/30_mc_in_flask.py"]=5009
    ["PE_Change/10_pe_de_flask.py"]=5010
    ["PE_Change/10_pe_in_flask.py"]=5011
    ["PE_Change/20_pe_de_flask.py"]=5012
    ["PE_Change/20_pe_in_flask.py"]=5013
    ["PE_Change/30_pe_de_flask.py"]=5014
    ["PE_Change/30_pe_in_flask.py"]=5015
    ["Price_de/10_price_de_flask.py"]=5016
    ["Price_de/15_Price_de_flask.py"]=5017
    ["Price_de/20_price_de_flask.py"]=5018
    ["Price_in/20_price_in_flask.py"]=5019
    ["Price_in/50_price_in_flask.py"]=5020
    ["Price_in/75_price_in_flask.py"]=5021
    ["Volume/1.125_volume_flask.py"]=5022
    ["Volume/1.25_volume_flask.py"]=5023
    ["Volume/1.5_volume_flask.py"]=5024
    ["Volume/1.75_volume_flask.py"]=5025
    ["Volume/2_volume_flask.py"]=5026
    ["Volume/2.5_volume_flask.py"]=5027
    ["Volume/3_volume_flask.py"]=5028
    ["Volume/5x_volume_flask.py"]=5029
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

# Start all non-email Flask apps using Python
for script in "${!apps[@]}"; do
    port=${apps[$script]}
    script_path="/home/ec2-user/Stock-Scanner-Project/$script"

    if [ -f "$script_path" ]; then
        nohup python "$script_path" > "$LOG_DIR/$(basename "$script" .py).log" 2>&1 &
        echo "Started $script_path on port $port"
    else
        echo "Error: $script_path not found!"
    fi
    sleep 2  # Short delay to avoid overloading system
done

echo "All Flask apps started. Now managing email scripts..."

# Function to manage email scripts based on New York time
manage_email_scripts() {
    while true; do
        # Get the current hour in New York (24-hour format)
        current_hour=$(TZ="America/New_York" date +%H)

        # Allowed if current hour is >= 8 OR < 5
        if (( 10#$current_hour >= 8 || 10#$current_hour < 5 )); then
            # Start or ensure email scripts are running
            for script in "${email_apps[@]}"; do
                script_path="/home/ec2-user/Stock-Scanner-Project/$script"
                script_name=$(basename "$script")

                if [ -f "$script_path" ]; then
                    if ! pgrep -f "$script_path" > /dev/null; then
                        nohup python "$script_path" > "$LOG_DIR/${script_name}.log" 2>&1 &
                        echo "Started $script_path (email group)"
                    fi
                else
                    echo "Error: $script_path not found!"
                fi
            done
        else
            # Stop email scripts outside allowed time window
            for script in "${email_apps[@]}"; do
                pkill -f "/home/ec2-user/Stock-Scanner-Project/$script"
                echo "Stopped $script (email group) outside allowed time."
            done
        fi
        sleep 60  # Check every minute
    done
}

# Run email script manager in background
manage_email_scripts &