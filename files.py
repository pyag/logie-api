from typing import List
import os
import datetime

from fastapi import APIRouter

from pydmodels.file_model import FileModel, FileDataModel

router = APIRouter()

@router.get("/files/", response_model=FileModel)
async def list_files():
    """Return a listing of files in the current directory.

    The response matches :class:`FileModel.FileModel` so the OpenAPI
    schema for `/files/` is generated correctly.
    """
    entries: List[FileDataModel] = []
    for fname in os.listdir("."):
        try:
            stat = os.stat(fname)
        except FileNotFoundError:
            continue
        file_type = "directory" if os.path.isdir(fname) else "file"
        size = str(stat.st_size)
        modified = datetime.datetime.fromtimestamp(stat.st_mtime).isoformat()
        entries.append(
            FileDataModel(
                name=fname,
                type=file_type,
                size=size,
                modified=modified,
            )
        )

    header = ["name", "type", "size", "modified"]
    return FileModel(header=header, data=entries)
