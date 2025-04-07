import boto3
from botocore.exceptions import NoCredentialsError

# Initialize the S3 client
s3 = boto3.client('s3')

# List of files to be uploaded
files = [
    "1.125_volume.json", "1.25_volume.json", "1.5_volume.json", "1.75_volume.json",
    "10_de_pe_subs.json", "10_in_pe_subs.json", "10_mc_de.json", "10_mc_in.json",
    "10_pe_de.json", "10_pe_in.json", "10_price_de.json", "100_DVSA.json",
    "15_price_de.json", "150_DVSA.json", "15w_price_de.json", "2.5_volume.json",
    "20_de_pe_subs.json", "20_in_pe_subs.json", "20_mc_de.json", "20_mc_in.json",
    "20_pe_de.json", "20_pe_in.json", "20_price_de.json", "20_price_in.json",
    "2x_volume.json", "30_de_pe_subs.json", "30_in_pe_subs.json", "30_mc_de.json",
    "30_mc_in.json", "30_pe_de.json", "30_pe_in.json", "3x_volume.json",
    "50_DVSA.json", "50_price_in.json", "5x_volume.json", "75_price_in.json"
]

# S3 bucket name
bucket_name = 'exportbucket--use2-az1--x-s3'

def upload_to_s3(file_name, bucket):
    try:
        s3.upload_file(file_name, bucket, file_name)
        print(f"Upload Successful: {file_name}")
    except FileNotFoundError:
        print(f"The file was not found: {file_name}")
    except NoCredentialsError:
        print("Credentials not available")

# Iterate through the list of files and upload each one
for file in files:
    upload_to_s3(file, bucket_name)
