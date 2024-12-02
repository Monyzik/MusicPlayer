from tinytag import TinyTag


class Track:
    def __init__(self, path):
        tag = TinyTag.get(path, image=True)

        self.path = path
        self.title = tag.title
        self.author = tag.artist
        self.image = tag.get_image()
        self.duration = tag.duration

    def __repr__(self):
        return f"{self.author} - {self.title}"

    def get_pretty_duration(self) -> str:
        return f"{int(self.duration / 60)}:{int(self.duration % 60) + 1:02}"

