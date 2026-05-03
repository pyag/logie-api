from typing import Annotated, List

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile

from pydmodels.file_model import FileModel, FileDataModel
from service.file import list_uploaded_files, upload_file_chunk
from service.session import get_current_user

router = APIRouter()

@router.get("/files/", response_model=FileModel)
async def list_files(user: Annotated[dict | None, Depends(get_current_user)] = None):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    entries_data = await list_uploaded_files(user["user_id"])
    entries: List[FileDataModel] = [FileDataModel(**entry) for entry in entries_data]

    header = ["name", "type", "size", "modified"]
    return FileModel(header=header, data=entries)


@router.post("/upload/chunk/")
async def upload_chunk(
    request: Request,
    file: UploadFile = File(...),
    upload_id: str = Form(...),
    filename: str = Form(...),
    file_type: str = Form(...),
    file_size: int = Form(...),
    chunk_index: int = Form(...),
    total_chunks: int = Form(...),
    user: Annotated[dict | None, Depends(get_current_user)] = None,
):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    result = await upload_file_chunk(
        file=file,
        uid=user["user_id"],
        upload_id=upload_id,
        filename=filename,
        file_type=file_type,
        file_size=file_size,
        chunk_index=chunk_index,
        total_chunks=total_chunks,
    )
    return result
