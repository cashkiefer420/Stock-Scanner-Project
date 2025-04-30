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

# Parallel arrays: script names and ports
scripts=(
    "DVSA.50_DVSA_flask"
    "DVSA.100_DVSA_flask"
    "DVSA.150_DVSA_flask"
    "MC_Change.10_mc_de_flask"
    "MC_Change.10_mc_in_flask"
    "MC_Change.20_mc_de_flask"
    "MC_Change.20_mc_in_flask"
    "MC_Change.30_mc_de_flask"
    "MC_Change.30_mc_in_flask"
    "PE_Change.10_pe_de_flask"
    "PE_Change.10_pe_in_flask"
    "PE_Change.20_pe_de_flask"
    "PE_Change.20_pe_in_flask"
    "PE_Change.30_pe_de_flask"
    "PE_Change.30_pe_in_flask"
    "Price_de.10_price_de_flask"
    "Price_de.15_Price_de_flask"
    "Price_de.20_price_de_flask"
    "Price_in.20_price_in_flask"
    "Price_in.50_price_in_flask"
    "Price_in.75_price_in_flask"
    "Volume.1_125_volume_flask"
    "Volume.1_25_volume_flask"
    "Volume.1_5_volume_flask"
    "Volume.1_75_volume_flask"
    "Volume.2_volume_flask"
    "Volume.2_5_volume_flask"
    "Volume.3_volume_flask"
    "Volume.5x_volume_flask"
    "Stock_search_up"
    "News_display"
    "personalized_stock_filter"
)

ports=(
    5001 5002 5003
    5004 5005 5006 5007 5008 5009
    5010 5011 5012 5013 5014 5015
    5016 5017 5018
    5019 5020 5021
    5022 5023 5024 5025 5026 5027 5028 5029
    5030 5031 5032
)

# Start Flask apps
echo "Starting Flask apps..."
for i in "${!scripts[@]}"; do
    script=${scripts[$i]}
    port=${ports[$i]}
    log_file="$LOG_DIR/${script}.log"

    if ! pgrep -f "gunicorn -w 1 -b 127.0.0.1:$port blueprint.$script:app" > /dev/null; then
        nohup gunicorn -w 1 -b 127.0.0.1:$port "blueprint.$script:app" > "$log_file" 2>&1 &
        echo "Started blueprint.$script on port $port"
    else
        echo "Already running: blueprint.$script on port $port"
    fi

    sleep 1
done

echo "All scripts started successfully."
