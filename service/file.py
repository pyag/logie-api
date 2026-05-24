import logging

from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import aiofiles
from fastapi import HTTPException, UploadFile
from fastapi.responses import FileResponse
from mimetypes import guess_extension
from tortoise.exceptions import IntegrityError

from dbmodels.file_model import File as FileDB
from enums.file import FileSource, FileType

ROOT_UPLOAD_DIR = Path.home() / "upload"
CHUNK_SIZE = 1024 * 1024

logger = logging.getLogger(__name__)


def _format_size(size: int) -> str:
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{round(size / 1024, 2)} KB"
    elif size < 1024 * 1024 * 1024:
        return f"{round(size / (1024 * 1024), 2)} MB"
    return f"{round(size / (1024 * 1024 * 1024), 2)} GB"


def _normalize_file_type(file_type: str) -> FileType:
    normalized = file_type.lower()
    if normalized.startswith("image/"):
        return FileType.IMAGE
    if normalized.startswith("video/"):
        return FileType.VIDEO
    if normalized.startswith("application/pdf"):
        return FileType.PDF
    return FileType.BINARY


async def upload_file_chunk(
    file: UploadFile,
    uid: str,
    upload_id: str,
    filename: str,
    file_type: str,
    file_size: int,
    chunk_index: int,
    total_chunks: int,
    pid: str,
) -> dict[str, Any]:
    now = datetime.now()
    year = now.strftime("%Y")
    month = now.strftime("%m")
    day = now.strftime("%d")

    base_path = ROOT_UPLOAD_DIR / upload_id / year / month / day / uid
    base_path.mkdir(parents=True, exist_ok=True)

    ext = guess_extension(file_type) or Path(filename).suffix or ".bin"
    if not ext.startswith('.'):
        ext = f".{ext}"

    destination = base_path / f"{upload_id}{ext}"

    write_mode = "ab"
    if chunk_index == 0 or not destination.exists():
        write_mode = "wb"

    async with aiofiles.open(destination, write_mode) as dest_file:
        while True:
            chunk = await file.read(CHUNK_SIZE)
            if not chunk:
                break
            await dest_file.write(chunk)

    completed = chunk_index >= total_chunks - 1
    if completed:
        await _save_file_metadata(
            uid=uid,
            filename=filename,
            file_type=file_type,
            file_size=file_size,
            location=str(destination),
            pid=pid,
        )

    return {
        "upload_id": upload_id,
        "completed": completed,
        "filename": filename,
    }


async def _save_file_metadata(
    uid: str,
    filename: str,
    file_type: str,
    file_size: int,
    location: str,
    pid: str,
) -> None:
    file_type_enum = _normalize_file_type(file_type)
    try:
        existing = await FileDB.get_or_none(location=location)
        if existing:
            existing.name = filename
            existing.size = file_size
            existing.file_type = file_type_enum
            await existing.save()
            return

        await FileDB.create(
            uid=uuid4(),
            name=filename,
            size=file_size,
            file_type=file_type_enum,
            location=location,
            source=FileSource.LOCAL,
            user_id=uid,
            parent_id=UUID(pid) if pid else None,
        )
    except IntegrityError:
        # Fallback to update existing if a duplicate unique constraint arises.
        existing = await FileDB.get_or_none(location=location)
        if existing:
            existing.name = filename
            existing.size = file_size
            existing.file_type = file_type_enum
            await existing.save()
    except Exception:
        # Fail silently for metadata save, but keep the upload stream working.
        pass


async def list_uploaded_files(user_id: str, pid: str) -> list[dict[str, str]]:
    file_entries: list[dict[str, str]] = []
    parent = await FileDB.get_or_none(uid=UUID(pid), user_id=user_id).first()
    files = await FileDB.filter(user_id=user_id, parent=parent).order_by('-created_at')

    for file_record in files:
        file_entries.append({
            "file_id": str(file_record.uid),
            "name": file_record.name,
            "type": file_record.file_type.value if file_record.file_type else "UNKNOWN",
            "hidden": file_record.hidden,
            "size": _format_size(file_record.size),
            "modified": file_record.created_at.isoformat(),
        })
    return file_entries


async def download_file(file_id: str, user_id: str | None = None) -> FileResponse:
    try:
        file_uuid = UUID(file_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid file ID")

    file_record = await FileDB.get_or_none(uid=file_uuid)
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")

    # Check if file is hidden
    if file_record.hidden:
        # If hidden, only allow download if user is the owner
        if not user_id or str(file_record.user_id) != user_id:
            raise HTTPException(status_code=403, detail="Permission denied to download the file")

    file_path = Path(file_record.location)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on server")

    return FileResponse(path=file_path, filename=file_record.name)


async def hide_file(file_id: str, user_id: str) -> dict[str, str]:
    try:
        file_uuid = UUID(file_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid file ID")

    file_record = await FileDB.get_or_none(uid=file_uuid)
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")

    if str(file_record.user_id) != user_id:
        raise HTTPException(status_code=403, detail="You do not have permission to hide this file")

    file_record.hidden = True
    await file_record.save()

    return {"message": "File hidden successfully", "file_id": file_id}


async def unhide_file(file_id: str, user_id: str) -> dict[str, str]:
    try:
        file_uuid = UUID(file_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid file ID")

    file_record = await FileDB.get_or_none(uid=file_uuid)
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")

    if str(file_record.user_id) != user_id:
        raise HTTPException(status_code=403, detail="You do not have permission to unhide this file")

    file_record.hidden = False
    await file_record.save()

    return {"message": "File unhidden successfully", "file_id": file_id}

async def delete_file(file_id: str, user_id: str) -> dict[str, str]:
    try:
        file_uuid = UUID(file_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid file ID")

    file_record = await FileDB.get_or_none(uid=file_uuid)
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")

    if str(file_record.user_id) != user_id:
        raise HTTPException(status_code=403, detail="You do not have permission to delete this file")

    # Delete the physical file
    file_path = Path(file_record.location)
    if file_path.exists():
        try:
            file_path.unlink()
        except Exception:
            # Log the error but continue to delete the database record
            logger.error(f"Failed to delete file at {file_path}, but will remove database record. Error: {e}")
            pass

    # Delete the database record
    await file_record.delete()

    return {"message": "File deleted successfully", "file_id": file_id}

async def create_folder(folder_name: str, pid: str, user_id: str) -> str:
    try:
        folder = await FileDB.create(
            uid=uuid4(),
            name=folder_name,
            size=0,
            file_type=FileType.FOLDER,
            location="",
            source=FileSource.LOCAL,
            user_id=user_id,
            parent_id=UUID(pid) if pid else None,
        )

        return str(folder.uid)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create folder: {str(e)}")
