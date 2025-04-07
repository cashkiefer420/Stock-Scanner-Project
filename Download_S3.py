import boto3
import os
import time
import schedule

# Initialize the S3 client
s3_client = boto3.client('s3')

# S3 bucket name
S3_BUCKET_NAME = "exportbucket--use2-az1--x-s3"

# List of files to download from S3 before uploading
files_to_download = [
    "news.json",
    "stock_data_export.json"
]

def download_files_from_s3():
    for file_name in files_to_download:
        try:
            local_file_path = os.path.join('', file_name)  # Assuming the JSON files are in the current directory
            s3_client.download_file(S3_BUCKET_NAME, file_name, local_file_path)
            print(f"Downloaded {file_name} to {local_file_path}")
        except Exception as e:
            print(f"Failed to download {file_name}: {e}")

# List of files to upload
files_to_upload = [
    "1.125_volume.json",
    "1.25_volume.json",
    "1.5_volume.json",
    "1.75_volume.json",
    "10_de_pe_subs.json",
    "10_in_pe_subs.json",
    "10_mc_de.json",
    "10_mc_in.json",
    "10_pe_de.json",
    "10_pe_in.json",
    "10_price_de.json",
    "100_DVSA.json",
    "15_price_de.json",
    "150_DVSA.json",
    "15w_price_de.json",
    "2.5_volume.json",
    "20_de_pe_subs.json",
    "20_in_pe_subs.json",
    "20_mc_de.json",
    "20_mc_in.json",
    "20_pe_de.json",
    "20_pe_in.json",
    "20_price_de.json",
    "20_price_in.json",
    "2x_volume.json",
    "30_de_pe_subs.json",
    "30_in_pe_subs.json",
    "30_mc_de.json",
    "30_mc_in.json",
    "30_pe_de.json",
    "30_pe_in.json",
    "3x_volume.json",
    "50_DVSA.json",
    "50_price_in.json",
    "5x_volume.json",
    "75_price_in.json"
]

def upload_files_to_s3():
    for file_name in files_to_upload:
        if os.path.exists(file_name):
            try:
                s3_client.upload_file(file_name, S3_BUCKET_NAME, file_name)
                print(f"Uploaded {file_name} to {S3_BUCKET_NAME}")
            except Exception as e:
                print(f"Failed to upload {file_name}: {e}")
        else:
            print(f"File {file_name} does not exist")

if __name__ == "__main__":
    download_files_from_s3()
    schedule.every(2).minutes.do(download_files_to_s3)
    while True:
        schedule.run_pending()
        time.sleep(1)
    upload_files_from_s3()
    schedule.every(5).minutes.do(upload_files_to_s3)
    while True:
        schedule.run_pending()
        time.sleep(1)
