from dataclasses import dataclass

@dataclass
class FileLinkDirectory:
    files:list[FileLink]
    directory_url:str
    directory:str

@dataclass
class FileLink:
    url: str
    filename: str
    source_page: str