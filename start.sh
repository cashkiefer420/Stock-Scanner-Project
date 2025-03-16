
#!/bin/bash

# Activate virtual environment (adjust the path as needed)
source /home/ec2-user/venv/bin/activate

# Ensure a logs directory exists
LOG_DIR="/home/ec2-user/Stock-Scanner-Project/logs"
mkdir -p "$LOG_DIR"

# Declare non-email Flask apps and their ports
declare -A apps=(
    ["50_DVSA_flask.py"]=5001
    ["100_DVSA_flask.py"]=5002
    ["150_DVSA_flask.py"]=5003
    ["10_mc_de_flask.py"]=5004
    ["10_mc_in_flask.py"]=5005
    ["20_mc_de_flask.py"]=5006
    ["20_mc_in_flask.py"]=5007
    ["30_mc_de_flask.py"]=5008
    ["30_mc_in_flask.py"]=5009
    ["10_pe_de_flask.py"]=5010
    ["10_pe_in_flask.py"]=5011
    ["20_pe_de_flask.py"]=5012
    ["20_pe_in_flask.py"]=5013
    ["30_pe_de_flask.py"]=5014
    ["30_pe_in_flask.py"]=5015
    ["10_price_de_flask.py"]=5016
    ["15_Price_de_flask.py"]=5017
    ["20_price_de_flask.py"]=5018
    ["20_price_in_flask.py"]=5019
    ["50_price_in_flask.py"]=5020
    ["75_price_in_flask.py"]=5021
    ["1.125_volume_flask.py"]=5022
    ["1.25_volume_flask.py"]=5023
    ["1.5_volume_flask.py"]=5024
    ["1.75_volume_flask.py"]=5025
    ["2_volume_flask.py"]=5026
    ["2.5_volume_flask.py"]=5027
    ["3_volume_flask.py"]=5028
    ["5x_volume_flask.py"]=5029
)

# Declare email-related scripts (including Email_filter.py) and their ports.
# These scripts will only run between 8 AM and 5 AM (New York time).
declare -A email_apps=(
    ["50_DVSA_email.py"]=5101
    ["100_DVSA_email.py"]=5102
    ["150_DVSA_email.py"]=5103
    ["10_mc_de_email.py"]=5104
    ["10_mc_in_email.py"]=5105
    ["20_mc_de_email.py"]=5106
    ["20_mc_in_email.py"]=5107
    ["30_mc_de_email.py"]=5108
    ["30_mc_in_email.py"]=5109
    ["10_pe_de_email.py"]=5110
    ["10_pe_in_email.py"]=5111
    ["20_pe_de_email.py"]=5112
    ["20_pe_in_email.py"]=5113
    ["30_pe_de_email.py"]=5114
    ["30_pe_in_email.py"]=5115
    ["10_price_de_email.py"]=5116
    ["15_Price_de_email.py"]=5117
    ["20_price_de_email.py"]=5118
    ["20_price_in_email.py"]=5119
    ["50_price_in_email.py"]=5120
    ["75_price_in_email.py"]=5121
    ["1.125_volume_email.py"]=5122
    ["1.25_volume_email.py"]=5123
    ["1.5_volume_email.py"]=5124
    ["1.75_volume_email.py"]=5125
    ["2_volume_email.py"]=5126
    ["2.5_volume_email.py"]=5127
    ["3_volume_email.py"]=5128
    ["5_volume_email.py"]=5129
    ["Email_filter.py"]=5130
)

# Start all non-email Flask apps
for script in "${!apps[@]}"; do
    port="${apps[$script]}"
    nohup python3 "blueprint/${script}" --port "$port" > "$LOG_DIR/${script}.log" 2>&1 &
    echo "Started $script on port $port"
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
        for script in "${!email_apps[@]}"; do
            port="${email_apps[$script]}"
            # Check if already running; if not, start it.
            if ! pgrep -f "$script" > /dev/null; then
                nohup python3 "blueprint/${script}" --port "$port" > "$LOG_DIR/${script}.log" 2>&1 &
                echo "Started $script on port $port (email group)"
            fi
        done
    else
        # Outside allowed window; kill email scripts if running
        for script in "${!email_apps[@]}"; do
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