from PyQt6.QtCore import QSize, QTimer, QModelIndex, Qt
from PyQt6.QtGui import QImage, QPixmap, QIcon, QAction
from PyQt6.QtWidgets import QMainWindow, QSlider, QListWidgetItem, QFileDialog, QPushButton, QLabel
from pygame import mixer
from tinytag import TinyTag

from Constants import PATH_TO_PLAY_IMAGE, PATH_TO_STOP_IMAGE, PATH_TO_UP_IMAGE, PATH_TO_NEXT_IMAGE, PATH_TO_PREV_IMAGE, \
    PATH_TO_VOLUME_IMAGE, PATH_TO_REPEATING_PRESSED_IMAGE, PATH_TO_REPEATING_UNPRESSED_IMAGE
from States import States
from Track import Track, get_pretty_time
from TrackCard import TrackCard
from TrackDataBaseModel import Tracks
from TrackLineWidget import TrackLineWidget
from UI.MainWindowUI import Ui_AudioPlayerMainWindow


class MainWindow(QMainWindow, Ui_AudioPlayerMainWindow):

    def __init__(self):
        super().__init__()

        self.setupUi(self)
        self.track_time_slider.setVisible(False)

        self.track_card: TrackCard | None = None

        self.tracks_queue: list[Track] = list()
        self.track_id = 0

        self.load_tracks_from_db()
        self.add_track_action.triggered.connect(self.select_file)
        self.play_stop_button.setFlat(True)
        mixer.init()

        self.current_track_time = 0

        self.updater = QTimer(self)
        self.updater.start(1000)

        self.updater.timeout.connect(self.update_time)
        self.updater.timeout.connect(self.update_sliders)
        self.sliders_to_update: list[QSlider] = [self.track_time_slider]

        self.tracks_listWidget.itemClicked.connect(self.selected_track)
        self.tracks_listWidget.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)

        self.action_delete = QAction("Удалить", self.tracks_listWidget)
        self.tracks_listWidget.addAction(self.action_delete)
        self.action_delete.triggered.connect(self.delete_track)

        self.play_stop_button.clicked.connect(self.play_stop_button_clicked)
        self.track_time_slider.sliderReleased.connect(self.update_slider_position_from_move)

        self.current_track: Track | None = None
        self.current_state: States | None = None
        self.repeating = False

    # загрузка всех ранее сохраненных треков из бд
    def load_tracks_from_db(self):
        tracks = Tracks.select()
        for track in tracks:
            try:
                self.add_track_to_list(Track(track.directory))
            except FileNotFoundError:
                qwery = Tracks.delete().where(Tracks.directory == track.directory)
                print(f"Найдено {qwery.execute()} неправильных записей, они удалены")

    # добавление трека в listWidget
    def add_track_to_list(self, track: Track):
        try:
            TinyTag.get(track.path, image=True)
        except FileNotFoundError:
            pass
        item = QListWidgetItem()
        widget = TrackLineWidget(track)
        self.tracks_listWidget.addItem(item)
        self.tracks_queue.append(track)
        self.tracks_listWidget.setItemWidget(item, widget)
        item.setSizeHint(QSize(self.tracks_listWidget.size().width() - 10, widget.size().height()))

    # выбор файла
    def select_file(self):
        path = QFileDialog.getOpenFileName(
            self, 'Выбрать картинку', '',
            'Медиа документ (*.mp3);')[0]
        if not path:
            return
        track = Track(path)
        print(track)
        if Tracks.select().where(Tracks.directory == track.path):
            print("Этот трек уже существует")
            return
        try:
            Tracks.create(title=track.title, author=track.author, image=track.image, duration=track.duration,
                      directory=path)
            self.add_track_to_list(track)
        except Exception:
            pass

    # выбор трека, вызывается при нажатии на определенный трек в listWidget
    def selected_track(self, item: QListWidgetItem):
        widget: TrackLineWidget = self.tracks_listWidget.itemWidget(item)
        track: Track = widget.track

        index: QModelIndex = self.tracks_listWidget.indexFromItem(item)
        print(index.row())
        self.track_id = index.row()

        self.current_track = track
        self.current_state = States.play
        self.update_state()

    # обработка нажатия на кнопку старт/стоп
    def play_stop_button_clicked(self):
        if self.current_state == States.play or self.current_state == States.resume:
            self.current_state = States.pause
            self.update_state()
        elif self.current_state == States.pause:
            self.current_state = States.resume
            self.update_state()

    # обновление всей информации о треке
    def update_information_of_track(self, track: Track, title_label: QLabel, author_label: QLabel,
                                    play_stop: QPushButton, track_image: QLabel):
        title_label.setText(track.title)
        author_label.setText(track.author)
        play_stop.setIcon(QIcon(PATH_TO_PLAY_IMAGE))
        play_stop.setIconSize(QSize(30, 30))

        image = QImage()
        image.loadFromData(track.image.data)
        image = image.scaled(track_image.size().height(), track_image.size().height())
        track_image.setPixmap(QPixmap.fromImage(image))

    # обновление состояния
    def update_state(self):
        track = self.current_track
        if self.current_state == States.play:
            self.track_time_slider.setVisible(True)
            self.more_button.setIcon(QIcon(PATH_TO_UP_IMAGE))
            self.more_button.clicked.connect(self.open_track_card_widget)
            self.repeating_button.clicked.connect(self.repeating_state_change)
            self.repeating_button.setIcon(QIcon(PATH_TO_REPEATING_UNPRESSED_IMAGE))
            self.update_information_of_track(track, self.current_title_label, self.current_author_label,
                                             self.play_stop_button, self.current_image_lable)

            self.current_duration_label.setText(track.get_pretty_duration_from_start(0))
            self.current_track_time = 0

            if self.track_card:
                self.update_information_of_track(track, self.track_card.track_name_label,
                                                 self.track_card.track_author_label, self.track_card.play_stop_button,
                                                 self.track_card.track_image_label)
                self.track_card.track_duration_label.setText(self.current_track.get_pretty_duration())
                self.current_track.get_pretty_duration_from_start(self.current_track_time)
            mixer.music.load(track.path)
            mixer.music.play()

        elif self.current_state == States.resume:
            self.play_stop_button.setIcon(QIcon(PATH_TO_PLAY_IMAGE))
            if self.track_card:
                self.track_card.play_stop_button.setIcon(QIcon(PATH_TO_PLAY_IMAGE))
            mixer.music.unpause()
        elif self.current_state == States.pause:
            self.play_stop_button.setIcon(QIcon(PATH_TO_STOP_IMAGE))
            if self.track_card:
                self.track_card.play_stop_button.setIcon(QIcon(PATH_TO_STOP_IMAGE))
            mixer.music.pause()
        elif self.current_state == States.stop:
            self.play_stop_button.setIcon(QIcon(PATH_TO_STOP_IMAGE))
            if self.track_card:
                self.track_card.play_stop_button.setIcon(QIcon(PATH_TO_STOP_IMAGE))
            mixer.music.stop()

    # обновление таймера
    def update_time(self):
        if self.current_state == States.pause or self.current_state == States.stop:
            return
        if not self.current_track:
            return
        self.current_track_time += 1
        if self.current_track_time > int(self.current_track.duration):
            if self.repeating:
                self.current_track_time = 0
                mixer.music.rewind()
            elif self.track_id == len(self.tracks_queue) - 1:
                self.current_state = States.stop
                self.update_state()
            else:
                self.next_track()
        self.current_duration_label.setText(self.current_track.get_pretty_duration_from_start(self.current_track_time))
        if self.track_card:
            self.track_card.cur_track_time_label.setText(get_pretty_time(self.current_track_time))

    # обновление статуса повтора трека
    def repeating_state_change(self):
        self.repeating ^= True
        if self.repeating:
            self.repeating_button.setIcon(QIcon(PATH_TO_REPEATING_PRESSED_IMAGE))
        else:
            self.repeating_button.setIcon(QIcon(PATH_TO_REPEATING_UNPRESSED_IMAGE))

    # Обновление слайдера (немного криво сделано, можно было добавить один if, но я добавил целый массив. Считайте это как эксперимент и не обращайте на это внимание)
    def update_sliders(self):
        for slider in self.sliders_to_update:
            try:
                slider.value()
            except RuntimeError:
                self.sliders_to_update.remove(slider)
                continue
            if self.current_state == States.play or self.current_state == States.resume or self.current_track_time != slider.value():
                slider.setMinimum(0)
                slider.setMaximum(int(self.current_track.duration))
                slider.setValue(self.current_track_time)

    # обновляет позицию слайдера после перемещения
    def update_slider_position_from_move(self):
        self.current_track_time = self.track_time_slider.value()
        print(f"Трек переместили на {self.current_track_time}")
        if self.current_state == States.play or self.current_state == States.resume:
            mixer.music.set_pos(self.current_track_time)
        self.update_sliders()
        self.current_duration_label.setText(self.current_track.get_pretty_duration_from_start(self.current_track_time))

    # удаление трека из бд и listWidget
    def delete_track(self):
        track: Track = self.tracks_listWidget.itemWidget(self.tracks_listWidget.currentItem()).track
        self.tracks_listWidget.takeItem(self.tracks_listWidget.currentRow())
        if track in self.tracks_queue:
            self.tracks_queue.remove(track)
        qwery = Tracks.delete().where(Tracks.directory == track.path)
        qwery.execute()

    # открытие карточки трека
    def open_track_card_widget(self):
        if self.track_card:
            return
        self.track_card = TrackCard(track=self.current_track, cur_time=self.current_track_time)
        self.sliders_to_update.append(self.track_card.track_slider)
        self.track_card.destroyed.connect(self.track_card_destroyed)
        self.track_card.show()

        self.track_card_updater = QTimer(self)
        self.track_card_updater.start(1000)
        self.track_card.track_slider.setValue(self.current_track_time)

        self.track_card.next_button.clicked.connect(self.next_track)
        self.track_card.next_button.setIcon(QIcon(PATH_TO_NEXT_IMAGE))
        self.track_card.next_button.setIconSize(QSize(20, 20))
        self.track_card.prev_button.clicked.connect(self.previous_track)
        self.track_card.prev_button.setIcon(QIcon(PATH_TO_PREV_IMAGE))
        self.track_card.prev_button.setIconSize(QSize(20, 20))

        if self.current_state in [States.resume, States.play]:
            self.track_card.play_stop_button.setIcon(QIcon(PATH_TO_PLAY_IMAGE))
        else:
            self.track_card.play_stop_button.setIcon(QIcon(PATH_TO_STOP_IMAGE))
        self.track_card.play_stop_button.setIconSize(QSize(30, 30))

        self.track_card.play_stop_button.clicked.connect(self.play_stop_button_clicked)
        self.track_card.track_slider.sliderReleased.connect(self.update_track_card_slider_position_from_move)
        self.track_card.track_slider.setValue(self.current_track_time)

        self.track_card.track_duration_label.setText(self.current_track.get_pretty_duration())
        self.track_card.cur_track_time_label.setText(get_pretty_time(self.current_track_time))

        self.track_card.volume_image.setIcon(QIcon(PATH_TO_VOLUME_IMAGE))
        self.track_card.volume_slider.setMaximum(100)
        self.track_card.volume_slider.setValue(int(mixer.music.get_volume() * 100))
        self.track_card.volume_slider.sliderReleased.connect(self.update_volume_from_slider_move)

    def update_volume_from_slider_move(self):
        volume: int = self.track_card.volume_slider.value()
        mixer.music.set_volume(volume / 100)

    # удаляет ненужные апдейты при закрытии карточки трека
    def track_card_destroyed(self):
        self.track_card_updater.stop()
        while self.track_card.track_slider in self.sliders_to_update:
            self.sliders_to_update.remove(self.track_card.track_slider)
        self.track_card = None

    # следующий трек
    def next_track(self):
        if self.track_id == len(self.tracks_queue) - 1:
            return
        self.current_state = States.play
        self.track_id += 1
        self.current_track = self.tracks_queue[self.track_id]
        self.update_state()

    # предыдущий трек
    def previous_track(self):
        if self.track_id == 0:
            return
        self.current_state = States.play
        self.track_id -= 1
        self.current_track = self.tracks_queue[self.track_id]
        self.update_state()

    # обновляет позицию слайдера в карточке трека после перемещения
    # (думал над тем как можно объединить обновление перемещения слайдера в основном окне и в карточке трека, в итоге пришел к тому,
    # что лучшее решение - написать две отдельные функции)
    def update_track_card_slider_position_from_move(self):
        self.current_track_time = self.track_card.track_slider.value()
        print(f"Трек переметили на {self.current_track_time}")
        if self.current_state == States.play or self.current_state == States.resume:
            mixer.music.set_pos(self.current_track_time)
        self.update_sliders()
        self.track_card.cur_track_time_label.setText(get_pretty_time(self.current_track_time))
