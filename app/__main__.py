from __future__ import annotations

import sys
from dataclasses import dataclass

from PySide6.QtCore import QObject, QThread, Signal
from PySide6.QtWidgets import (
    QApplication,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
    QPlainTextEdit,
)

from pipeline.config import DEFAULT_DAYS, DEFAULT_LANGUAGE, DEFAULT_MIN_RESULTS, DEFAULT_REGION
from pipeline.run import run_pipeline


@dataclass
class PipelineParams:
    topic: str
    language: str
    region: str
    days: int
    min_results: int


class PipelineWorker(QObject):
    finished = Signal(dict)
    failed = Signal(str)
    log = Signal(str)

    def __init__(self, params: PipelineParams) -> None:
        super().__init__()
        self.params = params

    def run(self) -> None:
        try:
            self.log.emit("Running pipeline...")
            result = run_pipeline(
                topic=self.params.topic,
                language=self.params.language,
                region=self.params.region,
                days=self.params.days,
                min_results=self.params.min_results,
            )
            self.finished.emit(result)
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))


class MainWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("YouTube Shorts Pipeline")

        self.topic_input = QLineEdit()
        self.language_input = QLineEdit(DEFAULT_LANGUAGE)
        self.region_input = QLineEdit(DEFAULT_REGION)

        self.days_input = QSpinBox()
        self.days_input.setRange(1, 3650)
        self.days_input.setValue(DEFAULT_DAYS)

        self.min_results_input = QSpinBox()
        self.min_results_input.setRange(1, 1000)
        self.min_results_input.setValue(DEFAULT_MIN_RESULTS)

        self.run_button = QPushButton("Run")
        self.run_button.clicked.connect(self._start_pipeline)

        self.status_label = QLabel("Ready")
        self.log_output = QPlainTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMaximumBlockCount(2000)

        form = QFormLayout()
        form.addRow("Topic", self.topic_input)
        form.addRow("Language", self.language_input)
        form.addRow("Region", self.region_input)
        form.addRow("Days", self.days_input)
        form.addRow("Min Shorts", self.min_results_input)

        button_row = QHBoxLayout()
        button_row.addWidget(self.run_button)
        button_row.addWidget(self.status_label)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addLayout(button_row)
        layout.addWidget(self.log_output)
        self.setLayout(layout)

        self._thread: QThread | None = None
        self._worker: PipelineWorker | None = None

    def _start_pipeline(self) -> None:
        topic = self.topic_input.text().strip()
        if not topic:
            self.status_label.setText("Topic is required")
            return

        self.run_button.setEnabled(False)
        self.status_label.setText("Running...")

        params = PipelineParams(
            topic=topic,
            language=self.language_input.text().strip() or DEFAULT_LANGUAGE,
            region=self.region_input.text().strip() or DEFAULT_REGION,
            days=self.days_input.value(),
            min_results=self.min_results_input.value(),
        )

        self._thread = QThread()
        self._worker = PipelineWorker(params)
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_finished)
        self._worker.failed.connect(self._on_failed)
        self._worker.log.connect(self._append_log)

        self._worker.finished.connect(self._thread.quit)
        self._worker.failed.connect(self._thread.quit)
        self._thread.finished.connect(self._cleanup_thread)

        self._thread.start()

    def _append_log(self, message: str) -> None:
        self.log_output.appendPlainText(message)

    def _on_finished(self, result: dict) -> None:
        self.status_label.setText(f"Done: {result.get('shorts_count', 0)} shorts")
        self.run_button.setEnabled(True)
        self._append_log(f"Result: {result}")

    def _on_failed(self, error: str) -> None:
        self.status_label.setText("Failed")
        self.run_button.setEnabled(True)
        self._append_log(f"Error: {error}")

    def _cleanup_thread(self) -> None:
        self._worker = None
        self._thread = None


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(520, 420)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
