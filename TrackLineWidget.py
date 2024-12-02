from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtWidgets import QWidget, QListWidgetItem
from PIL import Image

from Track import Track
from UI.TrackLineUI import Ui_TrackLine


class TrackLineWidget(QWidget, Ui_TrackLine):
    def __init__(self, track: Track):
        super().__init__()
        self.setupUi(self)
        self.track = track
        image = QImage()
        image.loadFromData(track.image)
        image = image.scaled(self.size().height(), self.size().height())
        self.image.setPixmap(QPixmap.fromImage(image))
        self.track_name.setText(track.title)
        self.duration.setText(track.get_pretty_duration())
        self.author.setText(track.author)




