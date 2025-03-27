from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from processing_api.utils.mongo_store import MongoDBClient, MongoCollections

app = FastAPI()

class Message(BaseModel):
    role: str
    content: str
class QueryRequest(BaseModel):
    project_id: str
    query: str


@app.post("/query/", response_model=dict)
async def process_query(request: QueryRequest):
    # Verify project exists
    mongo_client = MongoDBClient()
    project = mongo_client.get_by_id(
        collection_name=MongoCollections.FileProcessing.value,
        condition={"projectId": str(request.project_id)},
    )

    # Extract the last user message from the messages array
    last_user_message = next(
        (msg.content for msg in reversed(request.messages) if msg.role == "user"),
        None
    )

    if not last_user_message:
        raise HTTPException(
            status_code=400, detail="No user message found in the conversation"
        )
    if not project:
        raise HTTPException(
            status_code=404, detail=f"Project not found: {request.project_id}"
        )

    # TODO: Implement actual query processing
    # For now, return success response
    return {
        "status": "success",
        "project_id": request.project_id, 
        "message": {
            "role": "system",
            "content": f"Processed query for project {request.project_id}"
        }
    }


@app.get("/health")
async def health_check():
    return {"status": "ok"}
