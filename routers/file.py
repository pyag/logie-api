from typing import Annotated, List
import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile

from pydmodels.file_model import FileModel, FileDataModel, CreateNewFolderModel
from service.file import list_uploaded_files, upload_file_chunk, download_file, view_file, hide_file, unhide_file, delete_file, create_folder, list_public_locker_files
from service.session import get_current_user

router = APIRouter()

@router.get("/files/", response_model=FileModel)
async def list_files(
    pid: str,
    user: Annotated[dict, Depends(get_current_user)],
):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    entries_data = await list_uploaded_files(user["user_id"], pid)
    entries: List[FileDataModel] = [FileDataModel(**entry) for entry in entries_data]

    header = ["name", "type", "size", "modified", "Options/Actions"]
    return FileModel(header=header, data=entries)


@router.get("/download/{file_id}")
async def download_file_endpoint(
    file_id: str,
    user: Annotated[dict, Depends(get_current_user)],
):
    user_id = user["user_id"] if user else None
    return await download_file(file_id, user_id)


@router.get("/view/{file_id}")
async def view_file_endpoint(
    file_id: str,
    user: Annotated[dict | None, Depends(get_current_user)] = None,
):
    user_id = user["user_id"] if user else None
    return await view_file(file_id, user_id)


@router.post("/upload/chunk/")
async def upload_chunk(
    request: Request,
    user: Annotated[dict, Depends(get_current_user)],
    file: UploadFile = File(...),
    upload_id: str = Form(...),
    filename: str = Form(...),
    file_type: str = Form(...),
    file_size: int = Form(...),
    chunk_index: int = Form(...),
    total_chunks: int = Form(...),
    pid: str = Form(...),
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
        pid=pid,
    )
    return result


@router.post("/hide/{file_id}")
async def hide_file_endpoint(
    file_id: str,
    user: Annotated[dict, Depends(get_current_user)],
):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    result = await hide_file(file_id=file_id, user_id=user["user_id"])
    return result


@router.post("/unhide/{file_id}")
async def unhide_file_endpoint(
    file_id: str,
    user: Annotated[dict, Depends(get_current_user)],
):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    result = await unhide_file(file_id=file_id, user_id=user["user_id"])
    return result

@router.post("/delete/{file_id}")
async def delete_file_endpoint(
    file_id: str,
    user: Annotated[dict, Depends(get_current_user)],
):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    result = await delete_file(file_id=file_id, user_id=user['user_id'])
    return result

@router.post("/create_folder/")
async def create_folder_endpoint(
    body: CreateNewFolderModel,
    user: Annotated[dict, Depends(get_current_user)],
):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    folder_id = await create_folder(body.folder_name, body.pid, user['user_id'])
    return {
        "fid": folder_id,
        "message": "Folder created successfully"
    }


@router.get("/public/locker/{locker_uid}/files/", response_model=FileModel)
async def get_public_locker_files(
    locker_uid: str,
    pid: str,
):
    """
    Get non-hidden files from a public locker (no authentication required).
    
    Args:
        locker_uid: The UID of the locker owner
        pid: The parent folder ID to list files from (query parameter)
        
    Returns:
        FileModel with non-hidden files only
    """
    try:
        entries_data = await list_public_locker_files(locker_uid, pid)
        entries: list[FileDataModel] = [FileDataModel(**entry) for entry in entries_data]
        
        header = ["name", "type", "size", "modified", "download"]
        return FileModel(header=header, data=entries)
    except HTTPException:
        raise
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.exception(f"Error fetching public locker files for locker {locker_uid}")
        raise HTTPException(status_code=500, detail="Internal server error")
