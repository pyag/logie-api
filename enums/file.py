from enum import Enum

class FileType(str, Enum):
    FOLDER = "folder"
    VIDEO = "video"
    IMAGE = "image"
    PDF = "pdf"
    BINARY = "binary"

class FileSource(str, Enum):
    LOCAL = "LOCAL"
