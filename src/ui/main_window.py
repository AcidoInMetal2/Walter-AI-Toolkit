from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QFileDialog,
    QTextEdit,
    QLineEdit,
    QProgressBar,
    QCheckBox,
    QSpinBox,
    QGroupBox,
    QMessageBox,
    QSplitter,
)

from config.paths import TRANSCRIPTIONS_DIR
from src.core.context import Context
from src.modules.fileinfo.file_info import FileInfo
from src.services.obsidian_service import ObsidianService
from src.ui.drop_area import DropArea
from src.ui.transcription_worker import TranscriptionWorker
from src.ui.ai_review_worker import AIReviewWorker
from src.ui.post_diarization_worker import PostDiarizationWorker
from src.ui.settings_dialog import SettingsDialog


def _titulo_panel(texto: str) -> QLabel:
    lbl = QLabel(texto)
    lbl.setStyleSheet("font-size:9pt; font-weight:bold; color:#9aa0a6; padding:2px 2px 0 2px;")
    return lbl


class MainWindow(QMainWindow):

    def __init__(self):

        super().__init__()

        self.audio_path = ""
        self.worker: TranscriptionWorker | None = None
        self.ai_worker: AIReviewWorker | None = None
        self.post_diarize_worker: PostDiarizationWorker | None = None

        self.ultimo_context: Context | None = None
        self.ultimo_context_ia: Context | None = None
        self.campos_nombres: dict[str, QLineEdit] = {}

        self.carpeta_transcripciones: Path = TRANSCRIPTIONS_DIR
        self.carpeta_ia: Path = TRANSCRIPTIONS_DIR

        self.setWindowTitle("Walter AI Toolkit")

        self.resize(1150, 800)

        self.statusBar().showMessage("Esperando...")

        self.crear_ui()

    def crear_ui(self):

        central = QWidget()

        self.setCentralWidget(central)

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 8, 10, 6)
        layout.setSpacing(6)

        central.setLayout(layout)

        titulo = QLabel("🎤 Walter AI Toolkit")

        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        titulo.setStyleSheet("font-size:16px; font-weight:bold; padding:2px;")

        layout.addWidget(titulo)

        self.lblFaseEstado = QLabel()
        self.lblFaseEstado.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lblFaseEstado.setStyleSheet("""
            font-size:9.5pt; color:#c9cdd1; background:#2a2d31;
            border-radius:6px; padding:4px 8px; margin-bottom:2px;
        """)
        layout.addWidget(self.lblFaseEstado)
        self._set_estado(1, "Aguardando ingreso de archivo y carpetas de destino")

        # ============================================================
        # Splitter horizontal raíz: panel lateral (controles) a la
        # izquierda, contenido (los 3 paneles de texto) a la derecha.
        # setChildrenCollapsible(True) permite arrastrar el separador
        # hasta el borde y colapsar el panel lateral por completo.
        # ============================================================
        splitterRaiz = QSplitter(Qt.Orientation.Horizontal)
        splitterRaiz.setChildrenCollapsible(True)
        splitterRaiz.setHandleWidth(8)

        panelLateral = self._crear_panel_lateral()
        panelContenido = self._crear_panel_contenido()

        splitterRaiz.addWidget(panelLateral)
        splitterRaiz.addWidget(panelContenido)

        splitterRaiz.setStretchFactor(0, 0)
        splitterRaiz.setStretchFactor(1, 1)
        splitterRaiz.setSizes([260, 890])

        layout.addWidget(splitterRaiz, stretch=1)

        self.btnBuscar.clicked.connect(self.buscar_archivo)
        self.btnTranscribir.clicked.connect(self.transcribir)

    def _crear_panel_lateral(self) -> QWidget:
        """
        Panel izquierdo: todos los controles/acciones. Vive dentro del
        splitter raíz, así que el usuario puede arrastrar el borde para
        achicarlo, agrandarlo, o colapsarlo del todo.
        """
        panel = QWidget()
        panel.setMinimumWidth(0)

        layout = QVBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(8)
        panel.setLayout(layout)

        # --- Configuración ---
        self.btnConfiguracion = QPushButton("⚙ Configurar API Keys")
        self.btnConfiguracion.clicked.connect(self._abrir_configuracion)
        layout.addWidget(self.btnConfiguracion)

        # --- Archivo ---
        self.dropArea = DropArea()
        self.dropArea.archivoSoltado.connect(self.cargar_archivo)
        layout.addWidget(self.dropArea)

        self.btnBuscar = QPushButton("Seleccionar Archivo")
        layout.addWidget(self.btnBuscar)

        self.lblArchivo = QLabel("Ningún archivo seleccionado.")
        self.lblArchivo.setWordWrap(True)
        self.lblArchivo.setStyleSheet("""
        QLabel{
            background:#303134;
            border:1px solid #555;
            border-radius:6px;
            padding:6px 8px;
            font-size:9pt;
        }
        """)
        layout.addWidget(self.lblArchivo)

        self.btnTranscribir = QPushButton("Transcribir")
        self.btnTranscribir.setEnabled(False)
        layout.addWidget(self.btnTranscribir)

        carpeta_transcripciones_layout = QHBoxLayout()
        self.btnCarpetaTranscripciones = QPushButton("Carpeta destino")
        self.btnCarpetaTranscripciones.setToolTip(
            "Carpeta donde se guardan la transcripción y la transcripción con hablantes."
        )
        self.btnCarpetaTranscripciones.clicked.connect(self._elegir_carpeta_transcripciones)
        carpeta_transcripciones_layout.addWidget(self.btnCarpetaTranscripciones)
        layout.addLayout(carpeta_transcripciones_layout)

        self.lblCarpetaTranscripciones = QLabel(self._texto_carpeta(self.carpeta_transcripciones))
        self.lblCarpetaTranscripciones.setWordWrap(True)
        self.lblCarpetaTranscripciones.setToolTip(str(self.carpeta_transcripciones))
        self.lblCarpetaTranscripciones.setStyleSheet("font-size:8pt; color:#9aa0a6;")
        layout.addWidget(self.lblCarpetaTranscripciones)

        self.progressBar = QProgressBar()
        self.progressBar.setRange(0, 0)  # indeterminado: no sabemos el % real
        self.progressBar.setMaximumHeight(6)
        self.progressBar.setTextVisible(False)
        self.progressBar.setVisible(False)
        layout.addWidget(self.progressBar)

        # --- Diarización ---
        layout.addWidget(self._separador("DIARIZACIÓN"))

        self.chkDiarizar = QCheckBox("Detectar hablantes")
        layout.addWidget(self.chkDiarizar)

        self.lblCantidadHablantes = QLabel("Cantidad de hablantes:")
        self.lblCantidadHablantes.setEnabled(False)
        layout.addWidget(self.lblCantidadHablantes)

        self.spnCantidadHablantes = QSpinBox()
        self.spnCantidadHablantes.setRange(0, 20)
        self.spnCantidadHablantes.setValue(0)
        self.spnCantidadHablantes.setSpecialValueText("Automático")
        self.spnCantidadHablantes.setEnabled(False)
        self.spnCantidadHablantes.setToolTip(
            "0 = dejar que pyannote detecte automáticamente cuántos hablantes hay."
        )
        layout.addWidget(self.spnCantidadHablantes)

        self.chkDiarizar.toggled.connect(self.lblCantidadHablantes.setEnabled)
        self.chkDiarizar.toggled.connect(self.spnCantidadHablantes.setEnabled)

        self.btnContinuarDiarizacion = QPushButton("Continuar (diarizar ahora)")
        self.btnContinuarDiarizacion.setEnabled(False)
        self.btnContinuarDiarizacion.setToolTip(
            "Usá esto si ya transcribiste sin diarizar y ahora querés separar "
            "por hablantes, sin tener que repetir la transcripción entera."
        )
        self.btnContinuarDiarizacion.clicked.connect(self._diarizar_ahora)
        layout.addWidget(self.btnContinuarDiarizacion)

        # --- IA / Obsidian ---
        layout.addWidget(self._separador("IA Y OBSIDIAN"))

        self.btnCarpetaIA = QPushButton("Carpeta destino (resumen/análisis)")
        self.btnCarpetaIA.setToolTip(
            "Carpeta donde se guardan resumen.txt y analisis.txt. "
            "La nota final de Obsidian sigue yendo aparte, a su vault fijo."
        )
        self.btnCarpetaIA.clicked.connect(self._elegir_carpeta_ia)
        layout.addWidget(self.btnCarpetaIA)

        self.lblCarpetaIA = QLabel(self._texto_carpeta(self.carpeta_ia))
        self.lblCarpetaIA.setWordWrap(True)
        self.lblCarpetaIA.setToolTip(str(self.carpeta_ia))
        self.lblCarpetaIA.setStyleSheet("font-size:8pt; color:#9aa0a6;")
        layout.addWidget(self.lblCarpetaIA)

        self.btnGenerarIA = QPushButton("Generar resumen y análisis IA")
        self.btnGenerarIA.setEnabled(False)
        self.btnGenerarIA.clicked.connect(self._generar_ia)
        layout.addWidget(self.btnGenerarIA)

        self.btnGuardarObsidian = QPushButton("Guardar en Obsidian")
        self.btnGuardarObsidian.setEnabled(False)
        self.btnGuardarObsidian.clicked.connect(self._guardar_en_obsidian)
        layout.addWidget(self.btnGuardarObsidian)

        layout.addStretch()

        return panel

    @staticmethod
    def _separador(texto: str) -> QLabel:
        lbl = QLabel(texto)
        lbl.setStyleSheet("""
            font-size:8.5pt; font-weight:bold; color:#7a8085;
            padding-top:6px; border-top:1px solid #444;
        """)
        return lbl

    # --- Fase / Estado ---

    def _set_estado(self, fase: int, estado: str):
        nombres_fase = {
            1: "Fase 1 — Transcripción",
            2: "Fase 2 — Diarización",
            3: "Fase 3 — Resumen y Notas IA",
        }
        self.lblFaseEstado.setText(f"{nombres_fase.get(fase, f'Fase {fase}')}  •  Estado: {estado}")

    # --- Selección de carpetas de destino ---

    @staticmethod
    def _texto_carpeta(carpeta: Path) -> str:
        texto = str(carpeta)
        return texto if len(texto) <= 40 else "…" + texto[-38:]

    def _elegir_carpeta_transcripciones(self):
        carpeta = QFileDialog.getExistingDirectory(
            self, "Carpeta de destino para transcripciones", str(self.carpeta_transcripciones)
        )
        if carpeta:
            self.carpeta_transcripciones = Path(carpeta)
            self.lblCarpetaTranscripciones.setText(self._texto_carpeta(self.carpeta_transcripciones))
            self.lblCarpetaTranscripciones.setToolTip(str(self.carpeta_transcripciones))

    def _elegir_carpeta_ia(self):
        carpeta = QFileDialog.getExistingDirectory(
            self, "Carpeta de destino para resumen y análisis", str(self.carpeta_ia)
        )
        if carpeta:
            self.carpeta_ia = Path(carpeta)
            self.lblCarpetaIA.setText(self._texto_carpeta(self.carpeta_ia))
            self.lblCarpetaIA.setToolTip(str(self.carpeta_ia))

    def _abrir_configuracion(self):
        dialogo = SettingsDialog(self)
        dialogo.exec()

    def _crear_panel_contenido(self) -> QWidget:
        """
        Panel derecho: los tres paneles de texto, uno debajo del otro,
        dentro de un splitter vertical propio (independiente del splitter
        raíz) para poder redimensionar cada uno sin afectar al panel
        lateral.
        """
        contenedor = QWidget()
        layoutContenedor = QVBoxLayout()
        layoutContenedor.setContentsMargins(0, 0, 0, 0)
        contenedor.setLayout(layoutContenedor)

        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(8)

        # --- Sección 1: log en vivo de la transcripción ---
        seccionLog = QWidget()
        layoutLog = QVBoxLayout()
        layoutLog.setContentsMargins(0, 0, 0, 0)
        layoutLog.setSpacing(2)
        seccionLog.setLayout(layoutLog)

        layoutLog.addWidget(_titulo_panel("TRANSCRIPCIÓN (EN VIVO)"))

        self.txtTranscripcion = QTextEdit()
        self.txtTranscripcion.setReadOnly(True)
        self.txtTranscripcion.setPlaceholderText(
            "Acá va apareciendo la transcripción a medida que se genera..."
        )
        self.txtTranscripcion.setStyleSheet("""
        QTextEdit{
            background:#1e1f22;
            border:1px solid #555;
            border-radius:8px;
            padding:10px;
            font-family:Consolas, monospace;
            font-size:10pt;
        }
        """)
        layoutLog.addWidget(self.txtTranscripcion)

        splitter.addWidget(seccionLog)

        # --- Sección 2: hablantes + transcript final ---
        seccionHablantes = QWidget()
        layoutHablantes = QVBoxLayout()
        layoutHablantes.setContentsMargins(0, 0, 0, 0)
        layoutHablantes.setSpacing(2)
        seccionHablantes.setLayout(layoutHablantes)

        layoutHablantes.addWidget(_titulo_panel("TRANSCRIPT FINAL POR HABLANTE"))

        self.groupHablantes = QGroupBox("Hablantes detectados")
        self.groupHablantes.setVisible(False)
        self.groupHablantes.setMaximumHeight(140)

        group_layout = QVBoxLayout()
        group_layout.setContentsMargins(8, 6, 8, 6)
        self.groupHablantes.setLayout(group_layout)

        self.formHablantes = QFormLayout()
        group_layout.addLayout(self.formHablantes)

        acciones_hablantes = QHBoxLayout()

        self.btnAplicarNombres = QPushButton("Aplicar nombres")
        self.btnAplicarNombres.clicked.connect(self._aplicar_nombres)
        acciones_hablantes.addWidget(self.btnAplicarNombres)

        self.btnGuardarTranscript = QPushButton("Guardar transcript (.txt)")
        self.btnGuardarTranscript.clicked.connect(self._guardar_transcript_final)
        self.btnGuardarTranscript.setEnabled(False)
        acciones_hablantes.addWidget(self.btnGuardarTranscript)

        group_layout.addLayout(acciones_hablantes)

        layoutHablantes.addWidget(self.groupHablantes)

        self.txtTranscriptFinal = QTextEdit()
        self.txtTranscriptFinal.setReadOnly(True)
        self.txtTranscriptFinal.setPlaceholderText(
            "Acá va a aparecer el transcript final agrupado por hablante..."
        )
        self.txtTranscriptFinal.setStyleSheet("""
        QTextEdit{
            background:#232426;
            border:1px solid #555;
            border-radius:8px;
            padding:10px;
            font-size:10.5pt;
        }
        """)
        layoutHablantes.addWidget(self.txtTranscriptFinal)

        splitter.addWidget(seccionHablantes)

        # --- Sección 3: nota final de IA ---
        seccionIA = QWidget()
        layoutIA = QVBoxLayout()
        layoutIA.setContentsMargins(0, 0, 0, 0)
        layoutIA.setSpacing(2)
        seccionIA.setLayout(layoutIA)

        layoutIA.addWidget(_titulo_panel("NOTA GENERADA POR IA"))

        self.txtNotaIA = QTextEdit()
        self.txtNotaIA.setReadOnly(True)
        self.txtNotaIA.setPlaceholderText(
            "Acá va a aparecer la nota final generada por IA (resumen + análisis)..."
        )
        self.txtNotaIA.setStyleSheet("""
        QTextEdit{
            background:#20262b;
            border:1px solid #555;
            border-radius:8px;
            padding:10px;
            font-size:10.5pt;
        }
        """)
        layoutIA.addWidget(self.txtNotaIA)

        splitter.addWidget(seccionIA)

        splitter.setSizes([220, 260, 260])
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 1)

        layoutContenedor.addWidget(splitter)

        return contenedor

    def buscar_archivo(self):

        archivo, _ = QFileDialog.getOpenFileName(

            self,

            "Seleccione un Audio",

            "",

            "Audio/Video (*.mp3 *.wav *.m4a *.flac *.ogg *.opus *.aac *.mp4 *.mov *.mkv *.avi *.webm)"

        )

        if archivo:

            self.cargar_archivo(archivo)

    def cargar_archivo(self, archivo):

        self.audio_path = archivo

        info = FileInfo(archivo)

        self.lblArchivo.setText(
            f"📄 <b>{info.nombre}</b><br>{info.extension} &nbsp;•&nbsp; {info.tamano}"
        )
        self.lblArchivo.setToolTip(info.ruta)

        self.txtTranscripcion.clear()
        self._limpiar_panel_hablantes()
        self._limpiar_panel_ia()

        self.btnTranscribir.setEnabled(True)

        self._set_estado(1, "Aguardando ingreso de archivo y carpetas de destino")
        self.statusBar().showMessage("Archivo cargado correctamente")

    def transcribir(self):

        if not self.audio_path:
            return

        self.txtTranscripcion.clear()
        self._limpiar_panel_hablantes()
        self._limpiar_panel_ia()

        self.statusBar().showMessage("Transcribiendo...")
        self._set_estado(1, "Transcribiendo")

        self.btnBuscar.setEnabled(False)
        self.btnTranscribir.setEnabled(False)

        self.progressBar.setVisible(True)

        diarizar = self.chkDiarizar.isChecked()
        num_speakers = self.spnCantidadHablantes.value() or None  # 0 -> None (automático)

        self.worker = TranscriptionWorker(
            audio_path=self.audio_path,
            modelo="medium",
            idioma="Spanish",
            diarizar=diarizar,
            num_speakers=num_speakers,
            carpeta_transcripciones=self.carpeta_transcripciones,
        )

        self.worker.lineaRecibida.connect(self._agregar_linea)
        self.worker.finalizado.connect(self._transcripcion_finalizada)
        self.worker.error.connect(self._transcripcion_fallo)

        self.worker.start()

    def _agregar_linea(self, linea: str):
        self.txtTranscripcion.append(linea)

        if "Iniciando diarización" in linea:
            self._set_estado(2, "Diarizando transcripción")
        elif linea.startswith("[IA] Paso"):
            self._set_estado(3, "Creando resumen y notas IA")

    def _transcripcion_finalizada(self, context: Context):

        self.progressBar.setVisible(False)

        self.ultimo_context = context

        bloques = context.metadata.get("speaker_blocks")

        if bloques:
            self._armar_panel_hablantes(bloques)
            self._renderizar_transcript_final()
            self.groupHablantes.setVisible(True)
            self.btnGuardarTranscript.setEnabled(True)
            self.btnContinuarDiarizacion.setEnabled(False)  # ya se diarizó en esta corrida
            self._set_estado(2, "Ingreso manual de nombres de hablantes")
        else:
            self._limpiar_panel_hablantes()
            # Habilitamos "Continuar" solo si hay segmentos con timestamps
            # para cruzar (siempre los hay si Whisper terminó bien).
            self.btnContinuarDiarizacion.setEnabled(bool(context.transcript_segments))
            self._set_estado(1, "Transcripción finalizada")

        if context.transcript and context.transcript.strip():
            self.btnGenerarIA.setEnabled(True)

        self.statusBar().showMessage("Transcripción finalizada correctamente.")

        self.btnBuscar.setEnabled(True)
        self.btnTranscribir.setEnabled(True)

        # Whisper ya guarda sus salidas (txt/json/etc) de forma automática
        # en carpeta_transcripciones, así que avisamos apenas termina.
        QMessageBox.information(
            self,
            "Transcripción guardada",
            f"La transcripción se guardó en:\n\n{self.carpeta_transcripciones}",
        )

    def _transcripcion_fallo(self, mensaje: str):

        self.progressBar.setVisible(False)

        self.statusBar().showMessage(f"Error: {mensaje}")

        self.txtTranscripcion.append(f"\n[ERROR] {mensaje}")

        self.btnBuscar.setEnabled(True)
        self.btnTranscribir.setEnabled(True)

    # --- Diarización posterior (sin re-transcribir) ---

    def _diarizar_ahora(self):
        """
        Corre diarización + cruce con Whisper sobre la transcripción que
        ya está en self.ultimo_context, sin volver a llamar a Whisper.
        Pensado para cuando el usuario transcribió sin diarizar y recién
        después decide que sí quiere separar por hablantes.
        """
        if not self.ultimo_context or not self.ultimo_context.transcript_segments:
            self.statusBar().showMessage("No hay una transcripción con timestamps para diarizar.")
            return

        self.statusBar().showMessage("Diarizando sobre la transcripción ya generada...")
        self._set_estado(2, "Diarizando transcripción")

        self.btnBuscar.setEnabled(False)
        self.btnTranscribir.setEnabled(False)
        self.btnContinuarDiarizacion.setEnabled(False)

        self.progressBar.setVisible(True)

        num_speakers = self.spnCantidadHablantes.value() or None  # 0 -> None (automático)

        self.post_diarize_worker = PostDiarizationWorker(
            audio_path=self.audio_path,
            transcript_segments=self.ultimo_context.transcript_segments,
            num_speakers=num_speakers,
        )

        self.post_diarize_worker.lineaRecibida.connect(self._agregar_linea)
        self.post_diarize_worker.finalizado.connect(self._post_diarizacion_finalizada)
        self.post_diarize_worker.error.connect(self._post_diarizacion_fallo)

        self.post_diarize_worker.start()

    def _post_diarizacion_finalizada(self, context: Context):

        self.progressBar.setVisible(False)

        # Incorporamos el resultado al context que ya teníamos (conserva
        # transcript_segments, metadata previa, etc.) en vez de reemplazarlo.
        if self.ultimo_context:
            self.ultimo_context.diarization_segments = context.diarization_segments
            self.ultimo_context.metadata.update(context.metadata)
            self.ultimo_context.transcript = context.transcript

        bloques = context.metadata.get("speaker_blocks")

        if bloques:
            self._armar_panel_hablantes(bloques)
            self._renderizar_transcript_final()
            self.groupHablantes.setVisible(True)
            self.btnGuardarTranscript.setEnabled(True)
            self._set_estado(2, "Ingreso manual de nombres de hablantes")

        self.statusBar().showMessage("Diarización completada.")

        self.btnBuscar.setEnabled(True)
        self.btnTranscribir.setEnabled(True)

    def _post_diarizacion_fallo(self, mensaje: str):

        self.progressBar.setVisible(False)

        self.statusBar().showMessage(f"Error diarizando: {mensaje}")

        self.txtTranscripcion.append(f"\n[ERROR] {mensaje}")

        self.btnBuscar.setEnabled(True)
        self.btnTranscribir.setEnabled(True)
        self.btnContinuarDiarizacion.setEnabled(True)

    # --- Renombrado de hablantes ---

    def _armar_panel_hablantes(self, bloques: list[dict]):
        """
        Arma dinámicamente un campo de texto por cada hablante distinto
        detectado (en orden de primera aparición), para que el usuario
        pueda escribir el nombre real de cada uno.
        """
        self._limpiar_formulario_hablantes()

        vistos = []
        for bloque in bloques:
            if bloque["speaker"] not in vistos:
                vistos.append(bloque["speaker"])

        for speaker in vistos:
            campo = QLineEdit()
            campo.setPlaceholderText("Ej: Walter")
            self.formHablantes.addRow(f"{speaker}:", campo)
            self.campos_nombres[speaker] = campo

    def _limpiar_formulario_hablantes(self):
        while self.formHablantes.rowCount() > 0:
            self.formHablantes.removeRow(0)
        self.campos_nombres.clear()

    def _limpiar_panel_hablantes(self):
        self._limpiar_formulario_hablantes()
        self.groupHablantes.setVisible(False)
        self.txtTranscriptFinal.clear()
        self.btnGuardarTranscript.setEnabled(False)
        self.btnContinuarDiarizacion.setEnabled(False)

    def _aplicar_nombres(self):
        self._renderizar_transcript_final()
        self._set_estado(2, "Diarización finalizada")
        self.statusBar().showMessage("Nombres aplicados.")

    def _mapa_nombres(self) -> dict[str, str]:
        """
        Solo incluye hablantes a los que el usuario efectivamente les
        escribió un nombre; los que quedaron vacíos siguen mostrando
        su etiqueta original (SPEAKER_00, etc.).
        """
        return {
            speaker: campo.text().strip()
            for speaker, campo in self.campos_nombres.items()
            if campo.text().strip()
        }

    def _renderizar_transcript_final(self):

        if not self.ultimo_context:
            return

        bloques = self.ultimo_context.metadata.get("speaker_blocks", [])

        if not bloques:
            return

        mapa = self._mapa_nombres()

        texto = "\n\n".join(
            f"[{mapa.get(b['speaker'], b['speaker'])}] {b['text']}"
            for b in bloques
        )

        self.txtTranscriptFinal.setPlainText(texto)

    def _guardar_transcript_final(self):

        if not self.ultimo_context or not self.audio_path:
            return

        texto = self.txtTranscriptFinal.toPlainText()

        if not texto.strip():
            return

        self.carpeta_transcripciones.mkdir(parents=True, exist_ok=True)

        nombre_archivo = Path(self.audio_path).stem + "_con_hablantes.txt"
        destino = self.carpeta_transcripciones / nombre_archivo

        destino.write_text(texto, encoding="utf-8")

        self._set_estado(2, "Diarización finalizada")
        self.statusBar().showMessage(f"Guardado: {destino}")

        QMessageBox.information(
            self,
            "Diarización guardada",
            f"La transcripción con hablantes se guardó en:\n\n{self.carpeta_transcripciones}",
        )

    # --- Generación de resumen/análisis con IA ---

    def _texto_para_ia(self) -> str:
        """
        Prioriza el transcript final CON los nombres reales aplicados
        (si se corrió diarización y el usuario los puso). Si no hubo
        diarización, cae al transcript plano de Whisper.
        """
        texto_final = self.txtTranscriptFinal.toPlainText().strip()
        if texto_final:
            return texto_final

        if self.ultimo_context and self.ultimo_context.transcript:
            return self.ultimo_context.transcript

        return ""

    def _generar_ia(self):

        texto = self._texto_para_ia()

        if not texto.strip():
            self.statusBar().showMessage("No hay transcript disponible para analizar.")
            return

        self.statusBar().showMessage("Generando resumen y análisis con IA (Gemini)...")
        self._set_estado(3, "Creando resumen y notas IA")

        self.btnBuscar.setEnabled(False)
        self.btnTranscribir.setEnabled(False)
        self.btnGenerarIA.setEnabled(False)
        self.btnGuardarObsidian.setEnabled(False)

        self.progressBar.setVisible(True)

        self.ai_worker = AIReviewWorker(texto=texto)

        self.ai_worker.lineaRecibida.connect(self._agregar_linea)
        self.ai_worker.finalizado.connect(self._ia_finalizada)
        self.ai_worker.error.connect(self._ia_fallo)

        self.ai_worker.start()

    def _ia_finalizada(self, context: Context):

        self.progressBar.setVisible(False)

        self.ultimo_context_ia = context

        nota_final = context.metadata.get("nota_final", "")
        self.txtNotaIA.setPlainText(nota_final)

        self.btnGuardarObsidian.setEnabled(bool(nota_final.strip()))

        rutas_guardadas = self._guardar_intermedios_ia(context)

        self._set_estado(3, "Resumen y notas IA creados")

        mensaje = "Resumen y análisis generados correctamente."
        if rutas_guardadas:
            mensaje += f" Guardados en: {self.carpeta_ia}"
        self.statusBar().showMessage(mensaje)

        self.btnBuscar.setEnabled(True)
        self.btnTranscribir.setEnabled(True)
        self.btnGenerarIA.setEnabled(True)

        if rutas_guardadas:
            QMessageBox.information(
                self,
                "Resumen y Notas IA guardadas",
                f"El resumen y el análisis se guardaron en:\n\n{self.carpeta_ia}",
            )

    def _guardar_intermedios_ia(self, context: Context) -> list[Path]:
        """
        Guarda resumen y análisis como .txt planos en la carpeta elegida
        por el usuario, de forma automática (sin necesidad de que el
        usuario apriete ningún botón). Estos son datos de trabajo
        importantes que no deberían depender de que el usuario se
        acuerde de guardarlos.
        """
        if not self.audio_path:
            return []

        nombre_base = Path(self.audio_path).stem

        self.carpeta_ia.mkdir(parents=True, exist_ok=True)

        archivos = {
            "resumen": context.metadata.get("resumen", ""),
            "analisis": context.metadata.get("analisis", ""),
        }

        rutas = []
        for sufijo, contenido in archivos.items():
            if not contenido.strip():
                continue
            destino = self.carpeta_ia / f"{nombre_base}_{sufijo}.txt"
            destino.write_text(contenido, encoding="utf-8")
            rutas.append(destino)

        return rutas

    def _ia_fallo(self, mensaje: str):

        self.progressBar.setVisible(False)

        self.statusBar().showMessage(f"Error generando IA: {mensaje}")

        self.txtNotaIA.append(f"\n[ERROR] {mensaje}")

        self.btnBuscar.setEnabled(True)
        self.btnTranscribir.setEnabled(True)
        self.btnGenerarIA.setEnabled(True)

    def _limpiar_panel_ia(self):
        self.ultimo_context_ia = None
        self.txtNotaIA.clear()
        self.btnGuardarObsidian.setEnabled(False)
        self.btnGenerarIA.setEnabled(False)

    # --- Guardado en Obsidian ---

    def _guardar_en_obsidian(self):

        if not self.audio_path:
            return

        contenido = self.txtNotaIA.toPlainText()

        if not contenido.strip():
            return

        nombre_base = Path(self.audio_path).stem

        try:
            servicio = ObsidianService()
            destino = servicio.guardar_nota(nombre_base, contenido)
            self.statusBar().showMessage(f"Nota guardada en Obsidian: {destino}")
            QMessageBox.information(
                self,
                "Guardado en Obsidian",
                f"La nota se guardó correctamente en:\n\n{destino}",
            )
        except Exception as e:
            self.statusBar().showMessage(f"Error guardando en Obsidian: {e}")
            QMessageBox.critical(
                self,
                "Error al guardar en Obsidian",
                f"No se pudo guardar la nota:\n\n{e}",
            )
