from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
import os
import uuid

from processing_api.utils.storage import StorageConfig, StorageService
from processing_api.utils.archive_extractor import ArchiveExtractor
from processing_api.utils.producer import FileProducer
from processing_api.utils.mongo_store import MongoDBClient, MongoCollections


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
    file: UploadFile = File(...),
    storage: StorageService = Depends(get_storage_service),
):
    file_ext = file.filename.split(".")[-1]
    if file_ext not in ["zip", "gz", "tar"]:
        raise HTTPException(
            status_code=400, detail="Only a single zip/gz/tar.gz allowed!"
        )

    project_id = str(uuid.uuid4())

    extractor = ArchiveExtractor(
        file_name=file.filename, file_contents=await file.read(), project_id=project_id
    )
    extractor.extract_and_get_tree()

    file_producer = FileProducer()

    file_processing_status = []
    for dirpath, _, filenames in os.walk(project_id):
        for filename in filenames:
            full_path = os.path.join(dirpath, filename)
            try:
                with open(full_path, "r") as f:
                    storage.upload_file(file_content=f.read(), file_path=full_path)
                if not file_producer.send_message(
                    project_id=project_id, file_key=full_path
                ):
                    raise HTTPException(
                        status_code=500, detail="Failed to dump file tree into producer"
                    )

                file_processing_status.append(
                    {
                        "fullPath": full_path,
                        "docstringGeneration": False,
                        "libraryDocGeneration": False,
                        "rawCodeExtraction": False,
                    }
                )
            except:
                pass

    extractor.cleanup()

    mongo_client = MongoDBClient()
    mongo_client.put(
        collection_name=MongoCollections.FileProcessing.value,
        document={
            "projectId": project_id,
            "fileProcessingStatus": file_processing_status,
        },
    )

    return {"projectId": project_id}


@app.get("/project-status/{project_id}")
def get_project_status(project_id: str):
    mongo_client = MongoDBClient()
    return mongo_client.get_by_id(
        collection_name=MongoCollections.FileProcessing.value,
        condition={"projectId": str(project_id)},
    )


@app.get("/health")
async def health_check():
    return {"status": "ok"}
