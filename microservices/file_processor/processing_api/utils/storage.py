from pydantic import BaseModel
import boto3
from botocore.exceptions import ClientError
from datetime import datetime
import uuid
import os
from fastapi import HTTPException
import io
import tempfile
import tarfile


class StorageConfig(BaseModel):
    endpoint_url: str
    access_key: str
    secret_key: str
    bucket_name: str
    use_ssl: bool = False


class StorageService:
    def __init__(self, config: StorageConfig):
        self.config = config
        self.__client = self.__create_client()
        self.__ensure_bucket_exists()

    def __create_client(self):
        return boto3.client(
            "s3",
            endpoint_url=self.config.endpoint_url,
            aws_access_key_id=self.config.access_key,
            aws_secret_access_key=self.config.secret_key,
            use_ssl=self.config.use_ssl,
        )

    def __ensure_bucket_exists(self):
        try:
            # First, check if the bucket exists in the list of buckets
            existing_buckets = [
                bucket["Name"]
                for bucket in self.__client.list_buckets().get("Buckets", [])
            ]

            if self.config.bucket_name not in existing_buckets:
                self.__client.create_bucket(Bucket=self.config.bucket_name)
        except ClientError as e:
            if "InvalidLocationConstraint" in str(e):
                pass
            else:
                raise HTTPException(
                    status_code=500, detail=f"Storage configuration error: {str(e)}"
                )

    def create_tarball(self, files_data):
        tar_buffer = io.BytesIO()

        with tarfile.open(fileobj=tar_buffer, mode="w:gz") as tar:
            for filename, content in files_data:
                with tempfile.NamedTemporaryFile(delete=False) as temp:
                    temp.write(content)
                    temp_name = temp.name

                try:
                    tar.add(temp_name, arcname=filename)
                finally:
                    os.unlink(temp_name)

        tar_buffer.seek(0)
        return tar_buffer.read()

    def upload_tarball(self, tarball_content, original_filenames):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"upload_{timestamp}_{uuid.uuid4().hex}.tar.gz"

        try:
            self.__client.put_object(
                Bucket=self.config.bucket_name,
                Key=unique_filename,
                Body=tarball_content,
                ContentType="application/gzip",
            )

            return {
                "tarball_filename": unique_filename,
                "file_count": len(original_filenames),
                "tarball_size": len(tarball_content),
            }
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to upload tarball: {str(e)}"
            )
