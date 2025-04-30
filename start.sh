#!/bin/bash

# Dynamically set the project directory
PROJECT_DIR="$(pwd)"
LOG_DIR="$PROJECT_DIR/logs"

# Activate virtual environment
if [ -f "$PROJECT_DIR/.venv/bin/activate" ]; then
    source "$PROJECT_DIR/.venv/bin/activate"
else
    echo "Virtual environment not found at $PROJECT_DIR/.venv/"
    exit 1
fi

# Ensure gunicorn is installed in the venv
if ! command -v gunicorn &> /dev/null; then
    echo "⚠️ gunicorn not found in virtualenv. Installing it now..."
    pip install gunicorn
fi


# Ensure logs directory exists
mkdir -p "$LOG_DIR"

# Declare Flask apps with ports (use dot notation for blueprint compatibility)
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
    ["Volume.1_125_volume_flask"]=5022
    ["Volume.1_25_volume_flask"]=5023
    ["Volume.1_5_volume_flask"]=5024
    ["Volume.1_75_volume_flask"]=5025
    ["Volume.2_volume_flask"]=5026
    ["Volume.2_5_volume_flask"]=5027
    ["Volume.3_volume_flask"]=5028
    ["Volume.5x_volume_flask"]=5029
    ["Stock_search_up"]=5030
    ["personalized_stock_filter"]=5032
    ["News_display"]=5031
)

# Start all Flask apps using Gunicorn
echo "Starting Flask apps..."
nohup python3 "$PROJECT_DIR/Download_S3.py" > "$LOG_DIR/Download_S3.log" 2>&1 &
    echo "Started Download S3"
for script in "${!apps[@]}"; do
    port=${apps[$script]}
    log_file="$LOG_DIR/${script}.log"

    # Start Gunicorn if the script is not already running
    if ! pgrep -f "gunicorn -w 1 -b 127.0.0.1:$port blueprint.$script:app" > /dev/null; then
        nohup gunicorn -w 1 -b 127.0.0.1:$port blueprint.$script:app > "$log_file" 2>&1 &
        echo "Started blueprint.$script on port $port"
    else
        echo "Already running: blueprint.$script on port $port"
    fi
    sleep 2  # Avoid overloading system
done

echo "All scripts started successfully."
