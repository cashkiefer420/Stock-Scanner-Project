import boto3
import botocore

# AWS S3 Configuration
S3_BUCKET = "exportbucket--use2-az1--x-s3"
REGION = "us-east-2"
EXPORT_KEY = "stock_data_export.json"

# Initialize the S3 client
s3_client = boto3.client("s3", region_name=REGION)

def fetch_file_from_s3(bucket_name, key, download_path):
    try:
        # Download the file from S3
        s3_client.download_file(bucket_name, key, download_path)
        print(f"File '{key}' has been downloaded to '{download_path}'")
    except botocore.exceptions.ClientError as e:
        # Handle errors
        if e.response['Error']['Code'] == "404":
            print(f"The file '{key}' does not exist in bucket '{bucket_name}'.")
        else:
            print(f"An error occurred: {e}")

# Specify the local path to save the downloaded file
local_file_path = "./json/stock_data_export.json"

# Fetch the file
fetch_file_from_s3(S3_BUCKET, EXPORT_KEY, local_file_path)
