from pydantic import BaseModel

class FileDataModel(BaseModel):
    name: str
    type: str
    size: str
    modified: str

class FileModel(BaseModel):
    header: list[str]
    data: list[FileDataModel]

class FileListResponseModel(BaseModel):
    files: FileModel
