"""
Diálogo de configuración: permite cargar y guardar las API keys
(HF_TOKEN, GEMINI_API_KEY) directamente desde la app, sin depender de
variables de entorno del sistema.
"""
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QPushButton,
    QLabel,
    QMessageBox,
)

from config.settings import settings
from config.secrets_store import guardar_secrets


class SettingsDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Configuración - API Keys")
        self.setMinimumWidth(440)

        layout = QVBoxLayout()
        self.setLayout(layout)

        info = QLabel(
            "Estas claves se guardan localmente en tu PC "
            "(config/secrets.local.json), nunca se suben a GitHub."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color:#9aa0a6; font-size:9pt; padding-bottom:6px;")
        layout.addWidget(info)

        form = QFormLayout()
        layout.addLayout(form)

        self.txtHfToken = QLineEdit(settings.hf_token)
        self.txtHfToken.setEchoMode(QLineEdit.EchoMode.Password)
        self.txtHfToken.setPlaceholderText("hf_...")
        form.addRow("HF_TOKEN (HuggingFace):", self.txtHfToken)

        self.txtGeminiKey = QLineEdit(settings.gemini_api_key)
        self.txtGeminiKey.setEchoMode(QLineEdit.EchoMode.Password)
        self.txtGeminiKey.setPlaceholderText("AQ... o AIza...")
        form.addRow("GEMINI_API_KEY:", self.txtGeminiKey)

        fila_mostrar = QHBoxLayout()
        self.btnMostrar = QPushButton("👁 Mostrar")
        self.btnMostrar.setCheckable(True)
        self.btnMostrar.toggled.connect(self._toggle_mostrar)
        fila_mostrar.addWidget(self.btnMostrar)
        fila_mostrar.addStretch()
        layout.addLayout(fila_mostrar)

        layout.addSpacing(8)

        fila_botones = QHBoxLayout()

        btnGuardar = QPushButton("Guardar")
        btnGuardar.clicked.connect(self._guardar)
        fila_botones.addWidget(btnGuardar)

        btnCancelar = QPushButton("Cancelar")
        btnCancelar.clicked.connect(self.reject)
        fila_botones.addWidget(btnCancelar)

        layout.addLayout(fila_botones)

    def _toggle_mostrar(self, mostrar: bool):
        modo = QLineEdit.EchoMode.Normal if mostrar else QLineEdit.EchoMode.Password
        self.txtHfToken.setEchoMode(modo)
        self.txtGeminiKey.setEchoMode(modo)
        self.btnMostrar.setText("🙈 Ocultar" if mostrar else "👁 Mostrar")

    def _guardar(self):

        hf_token = self.txtHfToken.text().strip()
        gemini_key = self.txtGeminiKey.text().strip()

        settings.hf_token = hf_token
        settings.gemini_api_key = gemini_key

        guardar_secrets(hf_token=hf_token, gemini_api_key=gemini_key)

        QMessageBox.information(self, "Guardado", "Las claves se guardaron correctamente.")

        self.accept()
