from enum import Enum

class FileType(str, Enum):
    FOLDER = "FOLDER"
    VIDEO = "VIDEO"
    IMAGE = "IMAGE"
    BINARY = "BINARY"
