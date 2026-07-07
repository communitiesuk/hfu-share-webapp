from urllib.parse import quote

import boto3
from botocore.exceptions import ClientError

from case_management.settings import AWS_REGION

PRESIGNED_LINK_EXPIRY_SECONDS = 1000


def get_s3_client():
    return boto3.client("s3", region_name=AWS_REGION)


def get_file_header(bucket_name: str, file_key: str) -> dict:
    s3_client = get_s3_client()

    s3_response = s3_client.head_object(Bucket=bucket_name, Key=file_key)

    file_header = {
        "file_size": s3_response["ContentLength"],
        "file_format": s3_response["ContentType"],
        "last_modified": s3_response["LastModified"],
        "metadata": s3_response["Metadata"],
    }

    return file_header


def get_presigned_download_url(bucket_name: str, file_key: str, filename: str) -> str:
    s3_client = get_s3_client()

    # Ensure the file exists; generate_presigned_url throws no errors
    get_file_header(bucket_name, file_key)

    safe_filename = quote(filename, safe="")

    # Generate a presigned URL for downloading the file
    presigned_url = s3_client.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": bucket_name,
            "Key": file_key,
            "ResponseContentDisposition": f"attachment; filename={safe_filename}",
        },
        ExpiresIn=PRESIGNED_LINK_EXPIRY_SECONDS,
    )

    return presigned_url


def s3_file_exists(bucket_name: str, file_key: str):
    try:
        get_file_header(bucket_name=bucket_name, file_key=file_key)
        return True
    except ClientError:
        return False
