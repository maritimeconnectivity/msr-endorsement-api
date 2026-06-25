"""
    Desktop GUI for the MSR Validator.

    Replaces the FastAPI/Postman workflow: the user supplies the URL to test
    along with the public certificate, private key and root CA certificate, then
    clicks "Run tests". Each test result is displayed as soon as it is produced.
"""
import base64
import json
import logging
import os
import sys

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QFont
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.model.test_data import TestData
from app.model.test_result import TestResult
from app.model.test_results import TestResults
from app.test_scripts.msr_openapi_validator import MsrOpenApiValidator

# The OpenAPI schema lives alongside this file, regardless of the working directory.
SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "app", "schema", "MSRv2.json")

PASS_COLOUR = QColor("#1b7a37")
FAIL_COLOUR = QColor("#b3261e")


def _file_to_base64(path: str) -> str:
    """Read a certificate/key file and return its base64-encoded contents."""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")


class ValidatorWorker(QThread):
    """
        Runs the MSR validation on a background thread so the GUI stays
        responsive, emitting each result as soon as it is available.
    """

    result_ready = pyqtSignal(object)   # emits a TestResult
    finished_ok = pyqtSignal(object)    # emits the complete TestResults
    failed = pyqtSignal(str)            # emits an error message

    def __init__(self, test_data: TestData):
        super().__init__()
        self._test_data = test_data

    def run(self) -> None:
        try:
            validator = MsrOpenApiValidator(
                self._test_data,
                api_path=SCHEMA_PATH,
                progress_callback=self.result_ready.emit,
            )
            results: TestResults = validator.validate_msr()
            self.finished_ok.emit(results)
        except Exception as exc:  # surfaced to the user in the GUI
            logging.exception("Validation run failed")
            self.failed.emit(str(exc))


class FilePicker(QWidget):
    """A read-only line edit paired with a Browse button."""

    def __init__(self, dialog_title: str, name_filter: str):
        super().__init__()
        self._dialog_title = dialog_title
        self._name_filter = name_filter

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.line_edit = QLineEdit()
        self.line_edit.setPlaceholderText("No file selected")
        browse = QPushButton("Browse…")
        browse.clicked.connect(self._browse)

        layout.addWidget(self.line_edit)
        layout.addWidget(browse)

    def _browse(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, self._dialog_title, "",
                                              self._name_filter)
        if path:
            self.line_edit.setText(path)

    def path(self) -> str:
        return self.line_edit.text().strip()


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("MSR Validator")
        self.resize(900, 640)

        self._worker: ValidatorWorker | None = None

        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)

        # --- Input form -----------------------------------------------------
        form = QFormLayout()
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("https://example.com")
        self.public_picker = FilePicker("Select public certificate",
                                        "Certificates (*.pem *.crt *.cer);;All files (*)")
        self.private_picker = FilePicker("Select private key",
                                         "Keys (*.pem *.key);;All files (*)")
        self.root_picker = FilePicker("Select root CA certificate",
                                      "Certificates (*.pem *.crt *.cer);;All files (*)")
        self.instance_id_edit = QLineEdit()
        self.instance_id_edit.setPlaceholderText(
            "urn:mrn:mcp:service:...:instance:...")

        form.addRow("MSR URL:", self.url_edit)
        form.addRow("Public certificate:", self.public_picker)
        form.addRow("Private key:", self.private_picker)
        form.addRow("Root CA certificate:", self.root_picker)
        form.addRow("Test instance ID:", self.instance_id_edit)
        root_layout.addLayout(form)

        # --- Run button + status -------------------------------------------
        controls = QHBoxLayout()
        self.run_button = QPushButton("Run tests")
        self.run_button.clicked.connect(self._start)
        self.status_label = QLabel("Ready")
        controls.addWidget(self.run_button)
        controls.addWidget(self.status_label, stretch=1)
        root_layout.addLayout(controls)

        # --- Results tree ---------------------------------------------------
        self.results_tree = QTreeWidget()
        self.results_tree.setColumnCount(2)
        self.results_tree.setHeaderLabels(["Test", "Result"])
        self.results_tree.setColumnWidth(0, 600)
        root_layout.addWidget(self.results_tree, stretch=1)

        self._passed = 0
        self._total = 0

    # -- actions ------------------------------------------------------------
    def _start(self) -> None:
        url = self.url_edit.text().strip()
        public_path = self.public_picker.path()
        private_path = self.private_picker.path()
        root_path = self.root_picker.path()
        instance_id = self.instance_id_edit.text().strip()

        missing = []
        if not url:
            missing.append("MSR URL")
        if not public_path:
            missing.append("public certificate")
        if not private_path:
            missing.append("private key")
        if not root_path:
            missing.append("root CA certificate")
        if not instance_id:
            missing.append("test instance ID")
        if missing:
            QMessageBox.warning(self, "Missing input",
                                "Please provide: " + ", ".join(missing))
            return

        try:
            test_data = TestData(
                test_url=url,
                certificate=_file_to_base64(public_path),
                private_key=_file_to_base64(private_path),
                root_certificate=_file_to_base64(root_path),
                test_service_instance_id=instance_id,
            )
        except OSError as exc:
            QMessageBox.critical(self, "Could not read file", str(exc))
            return

        # Reset state for a fresh run
        self.results_tree.clear()
        self._passed = 0
        self._total = 0
        self.run_button.setEnabled(False)
        self.status_label.setText("Running tests…")

        self._worker = ValidatorWorker(test_data)
        self._worker.result_ready.connect(self._on_result)
        self._worker.finished_ok.connect(self._on_finished)
        self._worker.failed.connect(self._on_failed)
        self._worker.start()

    # -- worker callbacks ---------------------------------------------------
    def _on_result(self, result: TestResult) -> None:
        self._total += 1
        if result.test_success:
            self._passed += 1

        item = QTreeWidgetItem([result.test_name,
                                "PASS" if result.test_success else "FAIL"])
        colour = QBrush(PASS_COLOUR if result.test_success else FAIL_COLOUR)
        font = QFont()
        font.setBold(True)
        item.setForeground(1, colour)
        item.setFont(1, font)

        if result.failure_reason:
            item.addChild(QTreeWidgetItem(["Reason: " + result.failure_reason, ""]))
        if result.full_response:
            response = json.dumps(result.full_response, indent=2, default=str)
            item.addChild(QTreeWidgetItem(["Response: " + response, ""]))

        self.results_tree.addTopLevelItem(item)
        self.results_tree.scrollToItem(item)
        self.status_label.setText(
            f"Running tests… {self._passed}/{self._total} passed")

    def _on_finished(self, _results: TestResults) -> None:
        self._finish(f"Done — {self._passed}/{self._total} tests passed")

    def _on_failed(self, message: str) -> None:
        QMessageBox.critical(self, "Validation failed", message)
        self._finish("Run failed — see message")

    def _finish(self, status: str) -> None:
        self.status_label.setText(status)
        self.run_button.setEnabled(True)
        self._worker = None


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
