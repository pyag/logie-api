from pydantic import BaseModel

class FileDataModel(BaseModel):
    file_id: str
    name: str
    type: str
    hidden: bool
    size: str
    modified: str

class FileModel(BaseModel):
    header: list[str]
    data: list[FileDataModel]

class FileListResponseModel(BaseModel):
    files: FileModel

class CreateNewFolderModel(BaseModel):
    folder_name: str
    pid: str
