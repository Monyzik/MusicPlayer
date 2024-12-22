from PIL.ImageQt import QImage, QPixmap
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import QWidget

from Track import Track
from UI.TrackCardUI import Ui_TrackCardWidget


class TrackCard(QWidget, Ui_TrackCardWidget):
    def __init__(self, track: Track, cur_time: int):
        super().__init__()
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setupUi(self)

        self.track_slider.setValue(cur_time)

        self.set_information_of_track(track)

        # self.track = track

        # self.updater = QTimer(self)
        # self.updater.start(1000)
        # self.updater.timeout.connect(self.send)

    def set_information_of_track(self, track: Track):
        self.track_author_label.setText(track.author)
        self.track_name_label.setText(track.title)
        image = QImage()
        image.loadFromData(track.image.data)
        image = image.scaled(self.track_image_label.size().height(), self.track_image_label.size().height())
        self.track_image_label.setPixmap(QPixmap.fromImage(image))






