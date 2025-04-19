import os
import boto3
import json

# Environment Variables
S3_BUCKET = os.getenv("S3_BUCKET", "default-bucket-name")
REGION = os.getenv("REGION", "us-east-1")
EXPORT_KEY = "stock_data_export.json"
LOCAL_FILE_PATH = "stock_data_export.json"

# Initialize S3 Client
s3_client = boto3.client("s3", region_name=REGION)

def download_from_s3(bucket, key, local_path):
    """Download a file from S3."""
    try:
        print(f"Downloading {key} from S3 bucket {bucket}...")
        s3_client.download_file(bucket, key, local_path)
        print(f"Downloaded {key} to {local_path}")
    except Exception as e:
        print(f"Error downloading {key} from S3: {e}")

def update_local_file(local_path):
    """Update the local file."""
    try:
        if os.path.exists(local_path):
            print(f"Updating local file: {local_path}")
            with open(local_path, "r") as file:
                data = json.load(file)
            # Perform your update logic here
            data["updated"] = True
            with open(local_path, "w") as file:
                json.dump(data, file, indent=4)
            print(f"File {local_path} updated successfully.")
        else:
            print(f"Local file {local_path} does not exist. Skipping update.")
    except Exception as e:
        print(f"Error updating local file: {e}")

if __name__ == "__main__":
    # Download from S3
    download_from_s3(S3_BUCKET, EXPORT_KEY, LOCAL_FILE_PATH)
    
    # Update the local file
    update_local_file(LOCAL_FILE_PATH)
