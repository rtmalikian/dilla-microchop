#!/usr/bin/env python3
"""PySide6 desktop render/export app for Dilla Microchop."""

from __future__ import annotations

import json
import sys
import traceback
from dataclasses import asdict
from pathlib import Path

from PySide6.QtCore import QObject, QThread, QTimer, Signal
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QDoubleSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from microchop_sampler import PLAYBACK_MODES, STYLE_MODES, RenderConfig, RenderResult, render_job


class RenderWorker(QObject):
    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, config: RenderConfig) -> None:
        super().__init__()
        self.config = config

    def run(self) -> None:
        try:
            self.finished.emit(render_job(self.config))
        except Exception:
            self.failed.emit(traceback.format_exc())


class MicrochopWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.thread: QThread | None = None
        self.worker: RenderWorker | None = None
        self.setWindowTitle("Dilla Microchop")
        self.resize(820, 720)
        self._build_ui()

    def _build_ui(self) -> None:
        central = QWidget()
        layout = QVBoxLayout(central)
        self.setCentralWidget(central)

        file_box = QGroupBox("Files")
        file_layout = QGridLayout(file_box)
        self.sample_path = QLineEdit()
        self.midi_path = QLineEdit()
        self.output_dir = QLineEdit()
        self._file_row(file_layout, 0, "Sample", self.sample_path, self._pick_sample)
        self._file_row(file_layout, 1, "MIDI", self.midi_path, self._pick_midi)
        self._file_row(file_layout, 2, "Output", self.output_dir, self._pick_output_dir)
        layout.addWidget(file_box)

        settings = QGroupBox("Render Settings")
        form = QFormLayout(settings)
        self.target_track = QLineEdit("Main Melody")
        self.bar_start = self._spin(0, 999, 8)
        self.bar_count = self._spin(1, 999, 8)
        self.playback_mode = self._combo(PLAYBACK_MODES, "one-shot")
        self.style_mode = self._combo(STYLE_MODES, "fixed")
        self.min_chop_ms = self._double_spin(1.0, 2000.0, 45.0, 1.0)
        self.max_chop_ms = self._double_spin(1.0, 5000.0, 260.0, 1.0)
        self.onset_threshold = self._double_spin(0.001, 1.0, 0.08, 0.01)
        self.max_chops = self._spin(1, 5000, 256)
        self.max_pitch_shift = self._double_spin(0.0, 48.0, 12.0, 1.0)
        self.seed = self._spin(0, 999999999, 1337)

        form.addRow("Target track", self.target_track)
        form.addRow("Bar start", self.bar_start)
        form.addRow("Bar count", self.bar_count)
        form.addRow("Playback mode", self.playback_mode)
        form.addRow("Style mode", self.style_mode)
        form.addRow("Min chop ms", self.min_chop_ms)
        form.addRow("Max chop ms", self.max_chop_ms)
        form.addRow("Onset threshold", self.onset_threshold)
        form.addRow("Max chops", self.max_chops)
        form.addRow("Max pitch shift semitones", self.max_pitch_shift)
        form.addRow("Seed", self.seed)
        layout.addWidget(settings)

        actions = QHBoxLayout()
        self.render_button = QPushButton("Render")
        self.render_button.clicked.connect(self._render)
        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(self._clear)
        actions.addWidget(self.render_button)
        actions.addWidget(clear_button)
        actions.addStretch()
        layout.addLayout(actions)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        layout.addWidget(self.output, stretch=1)

    def _file_row(self, layout: QGridLayout, row: int, label: str, field: QLineEdit, picker) -> None:
        layout.addWidget(QLabel(label), row, 0)
        layout.addWidget(field, row, 1)
        button = QPushButton("Browse")
        button.clicked.connect(picker)
        layout.addWidget(button, row, 2)

    def _spin(self, minimum: int, maximum: int, value: int) -> QSpinBox:
        spin = QSpinBox()
        spin.setRange(minimum, maximum)
        spin.setValue(value)
        return spin

    def _double_spin(self, minimum: float, maximum: float, value: float, step: float) -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setRange(minimum, maximum)
        spin.setDecimals(3)
        spin.setSingleStep(step)
        spin.setValue(value)
        return spin

    def _combo(self, values: list[str], current: str) -> QComboBox:
        combo = QComboBox()
        combo.addItems(values)
        combo.setCurrentText(current)
        return combo

    def _pick_sample(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Choose sample", "", "Audio Files (*.wav *.aif *.aiff);;All Files (*)")
        if path:
            self.sample_path.setText(path)

    def _pick_midi(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Choose MIDI", "", "MIDI Files (*.mid *.midi);;All Files (*)")
        if path:
            self.midi_path.setText(path)

    def _pick_output_dir(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Choose output folder")
        if path:
            self.output_dir.setText(path)

    def _render(self) -> None:
        sample = self.sample_path.text().strip()
        midi = self.midi_path.text().strip()
        if not sample or not Path(sample).exists():
            QMessageBox.critical(self, "Missing sample", "Choose a local WAV or AIFF sample.")
            return
        if not midi or not Path(midi).exists():
            QMessageBox.critical(self, "Missing MIDI", "Choose a local MIDI file.")
            return

        config = RenderConfig(
            sample=sample,
            midi=midi,
            output_dir=self.output_dir.text().strip() or None,
            target_track=self.target_track.text().strip() or "Main Melody",
            bar_start=self.bar_start.value(),
            bar_count=self.bar_count.value(),
            playback_mode=self.playback_mode.currentText(),
            style_mode=self.style_mode.currentText(),
            min_chop_ms=self.min_chop_ms.value(),
            max_chop_ms=self.max_chop_ms.value(),
            onset_threshold=self.onset_threshold.value(),
            max_chops=self.max_chops.value(),
            max_pitch_shift_semitones=self.max_pitch_shift.value(),
            seed=self.seed.value(),
        )
        self._append("Rendering...\n")
        self.render_button.setEnabled(False)
        self.thread = QThread()
        self.worker = RenderWorker(config)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self._render_finished)
        self.worker.failed.connect(self._render_failed)
        self.worker.finished.connect(self.thread.quit)
        self.worker.failed.connect(self.thread.quit)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def _render_finished(self, result: RenderResult) -> None:
        self.render_button.setEnabled(True)
        self._append(json.dumps(asdict(result), indent=2) + "\n")

    def _render_failed(self, error: str) -> None:
        self.render_button.setEnabled(True)
        self._append("Render failed:\n" + error + "\n")
        QMessageBox.critical(self, "Render failed", error)

    def _append(self, text: str) -> None:
        self.output.append(text.rstrip())

    def _clear(self) -> None:
        self.output.clear()


def main() -> int:
    app = QApplication(sys.argv)
    window = MicrochopWindow()
    if "--smoke-window" in sys.argv:
        print(window.windowTitle())
        QTimer.singleShot(0, app.quit)
        return app.exec()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
