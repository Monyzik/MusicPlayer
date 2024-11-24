import sys
from MainWindowUI import Ui_AudioPlayerMainWindow
from TrackLine import Ui_Form
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import QApplication, QMainWindow, QFileDialog


class MainWindow(QMainWindow, Ui_AudioPlayerMainWindow):

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.action.triggered.connect(self.selectFile)

    def selectFile(self):
        fname = QFileDialog.getOpenFileName(
            self, 'Выбрать картинку', '',
            'Медиа документ (*.mp3)')[0]
        print(fname)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())