#!/bin/bash

# Activate virtual environment
source /home/ec2-user/venv/bin/activate

# Define project and logs directory
PROJECT_DIR="/home/ec2-user/Stock-Scanner-Project"
LOG_DIR="$PROJECT_DIR/logs"

# Ensure logs directory exists
mkdir -p "$LOG_DIR"

# Declare Flask apps with ports
declare -A apps=(
    ["Stock_search_up"]=5001
    ["personalized_stock_filter"]=5002
    ["News_display"]=5003
)

# Start all Flask apps using Gunicorn
echo "Starting Flask apps..."
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

# Declare other scripts
declare -A other_scripts=(
    ["Clean_News.py"]="clean_news.log"
    ["news.py"]="news.log"
    ["retrieve_data.py"]="retrieve_data.log"
)

# Start other scripts
echo "Starting other scripts..."
for script in "${!other_scripts[@]}"; do
    log_file="$LOG_DIR/${other_scripts[$script]}"
    nohup python "$PROJECT_DIR/blueprint/$script" > "$log_file" 2>&1 &
    echo "Started $script with log $log_file"
done

echo "All specified scripts started successfully."
