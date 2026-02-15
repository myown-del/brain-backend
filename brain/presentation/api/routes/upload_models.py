from pydantic import BaseModel


class ReadUploadedFileSchema(BaseModel):
    url: str
