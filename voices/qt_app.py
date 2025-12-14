import os
import sys

from PySide6 import QtCore, QtGui, QtWidgets

from transcriber import ses_dosyasini_texte_cevir


class TranscribeWorker(QtCore.QObject):
    progress = QtCore.Signal(int, int)  # total, current
    status = QtCore.Signal(str)
    finished = QtCore.Signal(str)  # output path
    error = QtCore.Signal(str)

    def __init__(self, audio_path: str, chunk_seconds: int, model_name: str) -> None:
        super().__init__()
        self.audio_path = audio_path
        self.chunk_seconds = chunk_seconds
        self.model_name = model_name

    @QtCore.Slot()
    def run(self) -> None:
        try:
            def on_progress(total: int, current: int) -> None:
                self.progress.emit(total, current)

            def on_status(text: str) -> None:
                self.status.emit(text)

            ses_dosyasini_texte_cevir(
                dosya_adi=self.audio_path,
                cikti_dosya=None,
                parca_suresi=self.chunk_seconds,
                model_adi=self.model_name,
                on_progress=on_progress,
                on_status=on_status,
            )
            base = os.path.splitext(os.path.basename(self.audio_path))[0]
            out_dir = os.path.dirname(self.audio_path)
            out_path = os.path.join(out_dir, f"{base}.txt")
            self.finished.emit(out_path)
        except Exception as exc:
            self.error.emit(str(exc))


class DropLineEdit(QtWidgets.QLineEdit):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, e: QtGui.QDragEnterEvent) -> None:
        if e.mimeData().hasUrls():
            e.acceptProposedAction()
        else:
            super().dragEnterEvent(e)

    def dropEvent(self, e: QtGui.QDropEvent) -> None:
        urls = e.mimeData().urls()
        if urls:
            local_path = urls[0].toLocalFile()
            if local_path:
                self.setText(local_path)
        super().dropEvent(e)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Whisper Transcriber")
        self.setMinimumSize(780, 500)
        self._build_ui()
        self._thread: QtCore.QThread | None = None

    def _build_ui(self) -> None:
        central = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(central)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # File selector
        file_row = QtWidgets.QHBoxLayout()
        self.file_edit = DropLineEdit()
        self.file_edit.setPlaceholderText(".m4a dosyası sürükle-bırak veya gözat…")
        browse_btn = QtWidgets.QPushButton("Gözat")
        browse_btn.clicked.connect(self._browse)
        file_row.addWidget(QtWidgets.QLabel("Ses Dosyası"))
        file_row.addWidget(self.file_edit, 1)
        file_row.addWidget(browse_btn)
        layout.addLayout(file_row)

        # Model + chunk controls
        controls_row = QtWidgets.QHBoxLayout()

        self.model_combo = QtWidgets.QComboBox()
        self.model_combo.addItems(["tiny", "base", "small", "medium", "large"])
        self.model_combo.setCurrentText("small")

        self.chunk_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.chunk_slider.setRange(10, 300)
        self.chunk_slider.setValue(60)
        self.chunk_slider.setTickPosition(QtWidgets.QSlider.TickPosition.TicksBelow)
        self.chunk_slider.setTickInterval(10)
        self.chunk_label = QtWidgets.QLabel("60 sn")
        self.chunk_slider.valueChanged.connect(lambda v: self.chunk_label.setText(f"{v} sn"))

        controls_row.addWidget(QtWidgets.QLabel("Model"))
        controls_row.addWidget(self.model_combo)
        controls_row.addSpacing(16)
        controls_row.addWidget(QtWidgets.QLabel("Parça Süresi"))
        controls_row.addWidget(self.chunk_slider, 1)
        controls_row.addWidget(self.chunk_label)
        layout.addLayout(controls_row)

        # Start + progress
        action_row = QtWidgets.QHBoxLayout()
        self.start_btn = QtWidgets.QPushButton("Dönüştür")
        self.start_btn.setDefault(True)
        self.start_btn.clicked.connect(self._start)
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        action_row.addWidget(self.start_btn)
        action_row.addWidget(self.progress_bar, 1)
        layout.addLayout(action_row)

        # Log output
        self.log = QtWidgets.QTextEdit()
        self.log.setReadOnly(True)
        self.log.setPlaceholderText("Durum mesajları burada görünecek…")
        layout.addWidget(self.log, 1)

        # Footer hint
        self.hint = QtWidgets.QLabel("Çıktı: seçilen dosyanın yanında .txt olarak oluşturulur.")
        self.hint.setStyleSheet("color: gray;")
        layout.addWidget(self.hint)

        self.setCentralWidget(central)

    def _browse(self) -> None:
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Ses dosyası seç", "", "M4A (*.m4a);;Tüm Dosyalar (*.*)")
        if path:
            self.file_edit.setText(path)

    def _set_busy(self, busy: bool) -> None:
        self.start_btn.setEnabled(not busy)
        self.file_edit.setEnabled(not busy)
        self.model_combo.setEnabled(not busy)
        self.chunk_slider.setEnabled(not busy)

    def _append_log(self, text: str) -> None:
        self.log.append(text)

    def _on_progress(self, total: int, current: int) -> None:
        if total <= 0:
            self.progress_bar.setRange(0, 0)
            return
        self.progress_bar.setRange(0, 100)
        pct = int((current / total) * 100)
        pct = max(0, min(100, pct))
        self.progress_bar.setValue(pct)

    def _start(self) -> None:
        audio_path = self.file_edit.text().strip()
        if not audio_path:
            QtWidgets.QMessageBox.warning(self, "Eksik bilgi", "Lütfen bir ses dosyası seçin.")
            return
        if not os.path.exists(audio_path):
            QtWidgets.QMessageBox.critical(self, "Dosya bulunamadı", audio_path)
            return

        chunk_seconds = int(self.chunk_slider.value())
        model_name = self.model_combo.currentText()

        self._set_busy(True)
        self.progress_bar.setValue(0)
        self.log.clear()
        self._append_log("İşlem başladı…")

        self._thread = QtCore.QThread(self)
        worker = TranscribeWorker(audio_path, chunk_seconds, model_name)
        worker.moveToThread(self._thread)

        # Connect signals
        self._thread.started.connect(worker.run)
        worker.progress.connect(self._on_progress)
        worker.status.connect(self._append_log)
        worker.finished.connect(self._on_finished)
        worker.error.connect(self._on_error)
        worker.finished.connect(self._thread.quit)
        worker.error.connect(self._thread.quit)
        worker.finished.connect(worker.deleteLater)
        worker.error.connect(worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)

        self._thread.start()

    @QtCore.Slot(str)
    def _on_finished(self, out_path: str) -> None:
        self._append_log("Tamamlandı.")
        self.progress_bar.setValue(100)
        self._set_busy(False)
        QtWidgets.QMessageBox.information(self, "Tamamlandı", f"Metin oluşturuldu:\n{out_path}")

    @QtCore.Slot(str)
    def _on_error(self, message: str) -> None:
        self._append_log(f"Hata: {message}")
        self._set_busy(False)
        QtWidgets.QMessageBox.critical(self, "Hata", message)


def apply_dark_theme(app: QtWidgets.QApplication) -> None:
    app.setStyle("Fusion")
    palette = QtGui.QPalette()
    dark = QtGui.QColor(45, 45, 48)
    near_black = QtGui.QColor(30, 30, 30)
    mid = QtGui.QColor(60, 60, 60)
    text = QtGui.QColor(220, 220, 220)
    disabled = QtGui.QColor(127, 127, 127)

    palette.setColor(QtGui.QPalette.Window, dark)
    palette.setColor(QtGui.QPalette.WindowText, text)
    palette.setColor(QtGui.QPalette.Base, near_black)
    palette.setColor(QtGui.QPalette.AlternateBase, dark)
    palette.setColor(QtGui.QPalette.ToolTipBase, text)
    palette.setColor(QtGui.QPalette.ToolTipText, text)
    palette.setColor(QtGui.QPalette.Text, text)
    palette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.Text, disabled)
    palette.setColor(QtGui.QPalette.Button, mid)
    palette.setColor(QtGui.QPalette.ButtonText, text)
    palette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.ButtonText, disabled)
    palette.setColor(QtGui.QPalette.BrightText, QtCore.Qt.red)
    palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor(45, 140, 240))
    palette.setColor(QtGui.QPalette.HighlightedText, QtCore.Qt.white)
    app.setPalette(palette)


def main() -> None:
    app = QtWidgets.QApplication(sys.argv)
    apply_dark_theme(app)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()


