import sys

from PySide6.QtWidgets import QApplication

from src.ui.main_window import MainWindow


def main():

    app = QApplication(sys.argv)

    ventana = MainWindow()

    ventana.show()

    sys.exit(app.exec())