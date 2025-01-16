import os
import importlib.util
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Define the blueprint directory
BLUEPRINT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "blueprint")

def import_and_run_scripts(directory):
    """Dynamically import and run all Python scripts in the specified directory."""
    for filename in os.listdir(directory):
        if filename.endswith(".py") and filename != "Init.py":
            script_path = os.path.join(directory, filename)
            module_name = filename[:-3]  # Remove '.py' extension
            
            logging.info(f"Running script: {filename}")

            try:
                # Load module dynamically
                spec = importlib.util.spec_from_file_location(module_name, script_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
            except Exception as e:
                logging.error(f"Error executing {filename}: {e}")

if __name__ == "__main__":
    logging.info("Initializing and running all scripts in blueprint folder...")
    import_and_run_scripts(BLUEPRINT_DIR)
    logging.info("All scripts executed.")