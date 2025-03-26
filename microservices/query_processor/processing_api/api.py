from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from processing_api.utils.mongo_store import MongoDBClient, MongoCollections

app = FastAPI()

class QueryRequest(BaseModel):
    project_id: str
    query: str

@app.post("/query/", response_model=dict)
async def process_query(request: QueryRequest):
    try:
        # Verify project exists
        mongo_client = MongoDBClient()
        project = mongo_client.get_by_id(
            collection_name=MongoCollections.FileProcessing.value,
            condition={"projectId": request.project_id}
        )
        
        if not project:
            raise HTTPException(
                status_code=404, 
                detail=f"Project not found: {request.project_id}"
            )

        # TODO: Implement actual query processing
        # For now, return success response
        return {
            "status": "success",
            "project_id": request.project_id,
            "results": []
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "ok"}