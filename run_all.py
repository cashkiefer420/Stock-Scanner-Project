import os
import subprocess
import threading
import time

# List of Python scripts to run
scripts = [
    "app/Init.py",
    "blueprints/Email_app_50_in_price.py",
    "blueprints/Email_filter.py",
    "blueprints/Splitter.py",
    "blueprints/Stock_search_up.py",
    "blueprints/email_app_10_de_price.py",
    "blueprints/email_app_10_mc_de.py",
    "blueprints/email_app_10_mc_in.py",
    "blueprints/email_app_10_pe_de.py",
    "blueprints/email_app_10_pe_in.py",
    "blueprints/email_app_15_de_price.py",
    "blueprints/email_app_20_de_price.py",
    "blueprints/email_app_20_in_price.py",
    "blueprints/email_app_20_mc_de.py",
    "blueprints/email_app_20_mc_in.py",
    "blueprints/email_app_20_pe_de.py,
    "blueprints/email_app_20_pe_in.py",
    "blueprints/email_app_30_mc_de.py",
    "blueprints/email_app_30_mc_in.py",
    "blueprints/email_app_30_pe_de.py",
    "blueprints/email_app_30_pe_in.py",
    "blueprints/email_app_75_in_price.py",
    "blueprints/email_app_fifty_volume.py",
    "blueprints/email_app_fivetimes_volume.py",
    "blueprints/email_app_onefifty_volume.py",
    "blueprints/email_app_onehundred_volume.py",
    "blueprints/email_app_ten_volume.py",
    "blueprints/email_app_threetimes_volume.py",
    "blueprints/email_app_twenty_volume.py",
    "blueprints/email_app_twotimes_volume.py",
    "blueprints/personalized_stock_filter.py",
    "blueprints/retrieve_data.py",
]

# Function to run a script and clear the terminal every 200 lines
def run_script(script_path):
    try:
        # Open the process and capture its output
        process = subprocess.Popen(
            ["python", script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        
        output_lines = 0
        
        for line in iter(process.stdout.readline, ""):
            print(line, end="")
            output_lines += 1

            # Clear terminal after 200 lines
            if output_lines >= 200:
                os.system("cls" if os.name == "nt" else "clear")
                output_lines = 0
        
        process.stdout.close()
        process.wait()
    except Exception as e:
        print(f"Error running {script_path}: {e}")

# Run all scripts in separate threads
threads = []
for script in scripts:
    thread = threading.Thread(target=run_script, args=(script,))
    threads.append(thread)
    thread.start()

# Wait for all threads to finish
for thread in threads:
    thread.join()

