from pydantic import BaseModel
import boto3


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
        # First, check if the bucket exists in the list of buckets
        existing_buckets = [
            bucket["Name"] for bucket in self.__client.list_buckets().get("Buckets", [])
        ]

        if self.config.bucket_name not in existing_buckets:
            raise ValueError(f"Cannot find bucket: {self.config.bucket_name}")

    def get_file(self, key: str):
        try:
            return self.__client.get_object(
                Bucket=self.config.bucket_name,
                Key=key,
            )
        except:
            raise ValueError(f"Cannot find key: {key}")

    def upload_file(self, file_content: str, file_path: str):
        self.__client.put_object(
            Bucket=self.config.bucket_name,
            Key=file_path,
            Body=file_content,
        )
