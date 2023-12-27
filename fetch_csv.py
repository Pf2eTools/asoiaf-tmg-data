import os
import boto3
from botocore import UNSIGNED
from botocore.config import Config
from pathlib import Path

# Based on
# https://github.com/chrisjd20/asoiaf_card_generator/blob/main/download_csvs.py


def main(filter_lang, filter_files):
    s3_client = boto3.client("s3", config=Config(signature_version=UNSIGNED))
    bucket_name = "asoif"
    prefix = "warcouncil/"
    paginator = s3_client.get_paginator("list_objects_v2")
    pages = paginator.paginate(Bucket=bucket_name, Prefix=prefix)

    version_files = {}
    for page in pages:
        for obj in page.get("Contents", []):
            key = obj["Key"]
            # It's a directory, skip
            if key.endswith("/"):
                continue
            _, version, filename = key.split("/")
            filename_split = filename.split(".")
            if len(filename_split) == 2:
                name, filetype = filename_split
                lang = "en"
            else:
                name, lang, filetype = filename_split
            if filetype != "csv":
                continue
            if lang not in filter_lang:
                continue
            if name not in filter_files:
                continue
            if version not in version_files:
                version_files[version] = []
            version_files[version].append(key)

    highest_version = max(version_files.keys())
    local_path = "./data/warcouncil"
    for file_key in version_files[highest_version]:
        local_file_path = os.path.join(local_path, os.path.basename(file_key))

        if not os.path.exists(local_path):
            Path(local_path).mkdir(parents=True, exist_ok=True)

        s3_client.download_file(bucket_name, file_key, local_file_path)
        print(f"Downloaded {file_key} to {local_file_path}")


if __name__ == "__main__":
    main(["de", "fr", "en"], ["units", "attachments", "tactics", "newskills", "ncus"])
