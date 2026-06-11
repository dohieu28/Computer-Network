import sys

from PyQt5.QtWidgets import QApplication
from module4_ui.MainWindow import MainWindow


# main.py (hiện tại)
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
