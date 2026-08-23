from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout
from PySide6.QtWidgets import QFileDialog

class DropArea(QFrame):

    archivoSoltado = Signal(str)

    def __init__(self):

        super().__init__()

        self.setAcceptDrops(True)

        self.setStyleSheet(self.estilo_normal())

        self.setMinimumHeight(200)
        self.setMaximumHeight(260)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        self.setLayout(layout)

        self.lblIcono = QLabel("🎤")
        self.lblIcono.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lblIcono.setStyleSheet("font-size:40px;")
        layout.addWidget(self.lblIcono)

        self.label = QLabel("Arrastrá un audio o video acá\no hacé clic para elegir un archivo")

        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setWordWrap(True)
        self.label.setStyleSheet("font-size:11pt;")

        layout.addWidget(self.label)

    def estilo_normal(self):

        return """
        QFrame{
            border:2px dashed gray;
            border-radius:10px;
        }
        """

    def estilo_hover(self):

        return """
        QFrame{
            border:2px dashed #3B82F6;
            background:#2E3C54;
            border-radius:10px;
        }
        """

    def dragEnterEvent(self, event):

        if event.mimeData().hasUrls():

            event.acceptProposedAction()
            self.setStyleSheet(self.estilo_hover())

        else:

            event.ignore()

    def dragLeaveEvent(self, event):

        self.setStyleSheet(self.estilo_normal())

    def dropEvent(self, event):

        self.setStyleSheet(self.estilo_normal())

        urls = event.mimeData().urls()

        if not urls:

            return

        archivo = urls[0].toLocalFile()

        self.archivoSoltado.emit(archivo)

    def mousePressEvent(self, event):

        archivo, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccione un Audio",
            "",
            "Audio/Video (*.mp3 *.wav *.m4a *.flac *.ogg *.opus *.aac *.mp4 *.mov *.mkv *.avi *.webm)"
        )

        if archivo:
            self.archivoSoltado.emit(archivo)

        super().mousePressEvent(event)
