import boto3
import os
import time
import schedule

# Initialize the S3 client
s3_client = boto3.client('s3')

# S3 bucket name
S3_BUCKET_NAME = "exportbucket--use2-az1--x-s3"

# List of files to download
files_to_download = [
    "news.json",
    "stock_data_export.json"
]

# Local JSON folder
LOCAL_JSON_FOLDER = "json"

def download_files_from_s3():
    for file_name in files_to_download:
        try:
            local_file_path = os.path.join(LOCAL_JSON_FOLDER, file_name)
            s3_client.download_file(S3_BUCKET_NAME, file_name, local_file_path)
            print(f"Downloaded {file_name} to {local_file_path}")
        except Exception as e:
            print(f"Failed to download {file_name}: {e}")

if __name__ == "__main__":
    schedule.every(2).minutes.do(download_files_from_s3)
    while True:
        schedule.run_pending()
        time.sleep(1)
