import sys

from PyQt6.QtCore import QFile, QTextStream
from PyQt6.QtWidgets import QApplication
import guidata.dataset.qtitemwidgets
from Player import MainWindow

if __name__ == '__main__':
    app = QApplication(sys.argv)
    file = QFile("UI/styles/black.qss")
    file.open(QFile.ReadOnly | QFile.Text)
    stream = QTextStream(file)
    app.setStyleSheet(stream.readAll())
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
