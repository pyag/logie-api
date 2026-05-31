from pathlib import Path

def delete_file_from_storage(location: str):
    """Delete a file from storage based on its location."""
    file_path = Path(location)
    if file_path.exists():
        file_path.unlink()
