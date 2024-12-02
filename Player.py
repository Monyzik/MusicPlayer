import sys

from PyQt6.QtCore import QSize, QUrl, QTimer
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.uic.properties import QtCore
from pyqtgraph.graphicsItems.ViewBox.ViewBoxMenu import translate

from TrackDataBaseModel import Tracks
from TrackLineWidget import TrackLineWidget
from UI.MainWindowUI import Ui_AudioPlayerMainWindow
from Track import Track
from PyQt6.QtWidgets import QApplication, QMainWindow, QFileDialog, QListWidgetItem, QAbstractItemView


class MainWindow(QMainWindow, Ui_AudioPlayerMainWindow):

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.load_tracks_from_db()
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.add_track_action.triggered.connect(self.select_file)
        self.tracks_listWidget.itemClicked.connect(self.selected_track)

    def load_tracks_from_db(self):
        tracks = Tracks.select()
        for track in tracks:
            self.add_track_to_list(Track(track.directory))

    def add_track_to_list(self, track: Track):
        item = QListWidgetItem()
        widget = TrackLineWidget(track)
        self.tracks_listWidget.addItem(item)
        self.tracks_listWidget.setItemWidget(item, widget)
        print(item)
        # item.setText(track.title)
        item.setSizeHint(QSize(self.tracks_listWidget.size().width() - 10, widget.size().height()))

    def select_file(self):
        path = QFileDialog.getOpenFileName(
            self, 'Выбрать картинку', '',
            'Медиа документ (*.mp3 *.wav);;All files (*)')[0]
        if not path:
            return
        track = Track(path)
        print(track)
        Tracks.create(title=track.title, author=track.author, image=track.image, duration=track.duration,
                      directory=path)
        self.add_track_to_list(track)

    def selected_track(self, item: QListWidgetItem):
        widget: TrackLineWidget = self.tracks_listWidget.itemWidget(item)
        track: Track = widget.track

        image = QImage()
        image.loadFromData(track.image)
        image = image.scaled(self.current_image_lable.size().height(), self.current_image_lable.size().height())
        self.current_image_lable.setPixmap(QPixmap.fromImage(image))

        self.current_title_label.setText(track.title)
        self.current_author_label.setText(track.author)
        self.current_duration_label.setText(track.get_pretty_duration())

        self.player.setSource(QUrl.fromLocalFile(track.path))
        self.player.play()
        self.player.stop()
        self.player.play()


