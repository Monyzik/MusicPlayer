import os
import sys
from queue import Queue

from PyQt6.QtCore import QSize, QUrl, QTimer, QModelIndex
from guidata.dataset.qtitemwidgets import LineEditWidget
from playhouse.sqlite_udf import duration
from pygame import mixer
from PyQt6.QtGui import QImage, QPixmap, QIcon
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput, QMediaFormat
from PyQt6.uic.properties import QtCore
from pygame.display import update
from pyqtgraph.graphicsItems.ViewBox.ViewBoxMenu import translate
from tinytag import TinyTag

from Constants import PATH_TO_PLAY_IMAGE, PATH_TO_STOP_IMAGE
from States import States
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
        self.add_track_action.triggered.connect(self.select_file)
        self.play_stop_button.setFlat(True)
        mixer.init()

        self.tracks_queue: Queue[Track] = Queue()

        self.current_track_time = 0

        self.updater = QTimer(self)
        self.updater.start(1000)

        self.updater.timeout.connect(self.update_time)
        self.updater.timeout.connect(self.update_slider)

        self.tracks_listWidget.itemClicked.connect(self.selected_track)
        self.play_stop_button.clicked.connect(self.play_stop_button_clicked)
        self.track_time_slider.sliderReleased.connect(self.update_slider_position_from_move)

        self.current_track: Track | None = None
        self.current_state: States | None = None

    def load_tracks_from_db(self):
        tracks = Tracks.select()
        for track in tracks:
            try:
                self.add_track_to_list(Track(track.directory))
            except FileNotFoundError:
                qwery = Tracks.delete().where(Tracks.directory == track.directory)
                print(f"Найдено {qwery.execute()} неправильных записей, они удалены")

    def add_track_to_list(self, track: Track):
        try:
            TinyTag.get(track.path, image=True)
        except FileNotFoundError:
            pass
        item = QListWidgetItem()
        widget = TrackLineWidget(track)
        self.tracks_listWidget.addItem(item)
        self.tracks_listWidget.setItemWidget(item, widget)
        item.setSizeHint(QSize(self.tracks_listWidget.size().width() - 10, widget.size().height()))

    def select_file(self):
        path = QFileDialog.getOpenFileName(
            self, 'Выбрать картинку', '',
            'Медиа документ (*.mp3 *.wav);;Все файлы (*)')[0]
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

        index: QModelIndex = self.tracks_listWidget.indexFromItem(item)
        print(index.row())
        for i in range(index.row() + 1, self.tracks_listWidget.count()):
            widget_from_index: LineEditWidget = self.tracks_listWidget.item(i)
            track_from_index: Track = self.tracks_listWidget.itemWidget(widget_from_index).track
            self.tracks_queue.put(track_from_index)
        # print(self.tracks_queue.get())

        self.current_track = track
        self.current_state = States.play
        self.update_state()

    def play_stop_button_clicked(self):
        if self.current_state == States.play or self.current_state == States.resume:
            self.current_state = States.pause
            self.update_state()
        elif self.current_state == States.pause:
            self.current_state = States.resume
            self.update_state()

    def update_state(self):
        track = self.current_track
        if self.current_state == States.play:
            self.current_title_label.setText(track.title)
            self.current_author_label.setText(track.author)
            self.current_duration_label.setText(track.get_pretty_duration_from_start(0))
            self.play_stop_button.setIcon(QIcon(PATH_TO_PLAY_IMAGE))
            self.play_stop_button.setIconSize(QSize(30, 30))

            self.current_track_time = 0

            image = QImage()
            image.loadFromData(track.image.data)
            image = image.scaled(self.current_image_lable.size().height(), self.current_image_lable.size().height())
            self.current_image_lable.setPixmap(QPixmap.fromImage(image))

            mixer.music.load(track.path)
            mixer.music.play()

        elif self.current_state == States.resume:
            self.play_stop_button.setIcon(QIcon(PATH_TO_PLAY_IMAGE))
            mixer.music.play()
            mixer.music.set_pos(self.current_track_time)
        elif self.current_state == States.pause:
            self.play_stop_button.setIcon(QIcon(PATH_TO_STOP_IMAGE))
            mixer.music.pause()
        elif self.current_state == States.stop:
            self.play_stop_button.setIcon(QIcon(PATH_TO_STOP_IMAGE))
            mixer.music.stop()

    def update_time(self):
        if self.current_state == States.pause or self.current_state == States.stop:
            return
        if not self.current_track:
            return
        self.current_track_time += 1
        if self.current_track_time > int(self.current_track.duration):
            if self.tracks_queue.empty():
                self.current_state = States.stop
                self.update_state()
            else:
                self.current_state = States.play
                self.current_track = self.tracks_queue.get()
                self.update_state()
        self.current_duration_label.setText(self.current_track.get_pretty_duration_from_start(self.current_track_time))

    def update_slider(self):
        if self.track_time_slider.value() != self.current_track_time - 1 and self.current_track_time > 2:
            return
        if self.current_state == States.play or self.current_state == States.resume:
            self.track_time_slider.setMinimum(0)
            self.track_time_slider.setMaximum(int(self.current_track.duration))
            self.track_time_slider.setValue(self.current_track_time)

    def update_slider_position_from_move(self):
        self.current_track_time = self.track_time_slider.value()
        print(self.current_track_time)
        if self.current_state == States.play or self.current_state == States.resume:
            mixer.music.set_pos(self.current_track_time)
        self.update_slider()
        self.current_duration_label.setText(self.current_track.get_pretty_duration_from_start(self.current_track_time))
