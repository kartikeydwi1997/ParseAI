from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from typing import List
import os

from processing_api.utils.storage import StorageConfig, StorageService


app = FastAPI()


def get_storage_service():
    endpoint_host = os.environ.get("STORAGE_HOST")
    endpoint_port = os.environ.get("STORAGE_PORT")

    config = StorageConfig(
        endpoint_url=f"http://{endpoint_host}:{endpoint_port}",
        access_key=os.environ.get("STORAGE_ACCESS_KEY"),
        secret_key=os.environ.get("STORAGE_SECRET_KEY"),
        bucket_name=os.environ.get("STORAGE_BUCKET_NAME"),
    )
    return StorageService(config)


@app.post("/upload/", response_model=dict)
async def upload_files(
    files: List[UploadFile] = File(...),
    storage: StorageService = Depends(get_storage_service),
):
    """
    Upload multiple files to MinIO/S3 (maximum 50 files)

    Returns a list of metadata for each uploaded file
    """
    # Check number of files
    if len(files) > 50:
        raise HTTPException(
            status_code=400, detail="Maximum 50 files allowed per upload"
        )

    if len(files) == 0:
        raise HTTPException(status_code=400, detail="No files provided")

    files_data = []
    original_filenames = []

    for file in files:
        # Read file content
        file_content = await file.read()
        files_data.append((file.filename, file_content))
        original_filenames.append(file.filename)

    # Create tarball from all files
    try:
        tarball_content = storage.create_tarball(files_data)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create tarball: {str(e)}"
        )

    # Upload the tarball
    result = storage.upload_tarball(tarball_content, original_filenames)

    return result


@app.get("/health")
async def health_check():
    return {"status": "ok"}
