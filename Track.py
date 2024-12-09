import io

from PIL import Image
from PyQt6.QtGui import QColor
from tinytag import TinyTag, Image


class Track:
    def __init__(self, path: str) -> None:
        tag = TinyTag.get(path, image=True)
        self.path = path
        self.title = tag.title
        self.author = tag.artist
        self.image: Image | None = tag.images.any
        self.duration = tag.duration

    def __repr__(self) -> str:
        return f"{self.author} - {self.title}"

    def get_pretty_duration(self) -> str:
        return f"{int(self.duration / 60)}:{int(self.duration % 60) + 1:02}"

    def get_pretty_duration_from_start(self, time) -> str:
        return f'{int(time / 60)}:{int(time % 60):02}/{self.get_pretty_duration()}'

