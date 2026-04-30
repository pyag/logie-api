from enum import Enum

class FileType(str, Enum):
    FOLDER = "FOLDER"
    VIDEO = "VIDEO"
    IMAGE = "IMAGE"
    BINARY = "BINARY"

class FileSource(str, Enum):
    LOCAL = "LOCAL"

