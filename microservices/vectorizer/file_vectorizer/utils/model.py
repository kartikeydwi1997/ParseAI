from pydantic import BaseModel


class QueueMessage(BaseModel):
    project_id: str


class FileProcessingStatus(BaseModel):
    fileKey: str
    docstringGeneration: str
    libraryDocGeneration: str
    rawCodeExtraction: str


class FileContents(BaseModel):
    docStringContent: str
    libraryDocStringContent: str
    rawCodeContent: str
    prompt: str
