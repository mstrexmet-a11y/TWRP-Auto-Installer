import webbrowser
from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QFrame, QMessageBox)
from core.adb import read_device, read_fastboot
from core.twrp_finder import find_official_pages

class ScanThread(QThread):
    done = Signal(object, object)
    def run(self):
        device = read_device()
        fastboot = read_fastboot()
        self.done.emit(device, fastboot)

class SearchThread(QThread):
    done = Signal(object, object)
    def __init__(self, device):
        super().__init__()
        self.device = device
    def run(self):
        try:
            self.done.emit(find_official_pages(self.device), None)
        except Exception as exc:
            self.done.emit([], str(exc))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TWRP Auto Installer")
        self.resize(900, 650)
        self.device = None
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        title = QLabel("TWRP AUTO INSTALLER")
        title.setStyleSheet("font-size:25px;font-weight:800;color:#e8edf7")
        subtitle = QLabel("Android device detection • Bootloader diagnostics • Official recovery search")
        subtitle.setStyleSheet("color:#9aa8bd")
        layout.addWidget(title)
        layout.addWidget(subtitle)
        panel = QFrame()
        panel.setStyleSheet("QFrame{background:#202938;border:1px solid #344256;border-radius:12px}")
        p = QVBoxLayout(panel)
        self.status = QLabel("Connect an Android device with USB debugging enabled, then scan.")
        self.status.setWordWrap(True)
        self.status.setStyleSheet("font-size:15px;color:#f1f5fb;padding:8px")
        p.addWidget(self.status)
        row = QHBoxLayout()
        self.scan_btn = QPushButton("Scan device")
        self.scan_btn.clicked.connect(self.scan)
        self.search_btn = QPushButton("Find official TWRP")
        self.search_btn.setEnabled(False)
        self.search_btn.clicked.connect(self.search)
        row.addWidget(self.scan_btn); row.addWidget(self.search_btn)
        p.addLayout(row)
        layout.addWidget(panel)
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setPlaceholderText("Device details and search results will appear here…")
        layout.addWidget(self.log, 1)
        warning = QLabel("Safety: this MVP never unlocks or flashes automatically. Unlocking may erase data; only use recovery builds explicitly made for your exact device.")
        warning.setWordWrap(True)
        warning.setStyleSheet("color:#e7bd75;padding:8px")
        layout.addWidget(warning)
        self.setStyleSheet("""
            QMainWindow{background:#111824}
            QLabel{color:#e7edf7}
            QPushButton{background:#3867d6;color:white;border:0;border-radius:8px;padding:11px 18px;font-weight:600}
            QPushButton:disabled{background:#465064;color:#aab2bf}
            QTextEdit{background:#172130;color:#dbe5f3;border:1px solid #344256;border-radius:10px;padding:10px}
        """)

    def scan(self):
        self.scan_btn.setEnabled(False)
        self.status.setText("Scanning ADB and Fastboot…")
        self.log.clear()
        self.worker = ScanThread()
        self.worker.done.connect(self.scan_done)
        self.worker.start()

    def scan_done(self, device, fastboot):
        self.scan_btn.setEnabled(True)
        self.device = device
        if device:
            self.status.setText(f"Detected: {device.get('manufacturer')} {device.get('model')} • ADB")
            self.log.append("DEVICE INFORMATION")
            for key in ("manufacturer", "model", "codename", "android", "build", "serial"):
                self.log.append(f"{key.title()}: {device.get(key, 'Unknown')}")
            self.search_btn.setEnabled(True)
        elif fastboot:
            self.status.setText(f"Detected Fastboot device • {fastboot['bootloader']}")
            self.log.append(f"Fastboot serial: {fastboot['serial']}")
            self.log.append(f"Bootloader: {fastboot['bootloader']}")
            self.log.append("\nFastboot mode may not expose model/codename. Reboot to Android and scan via ADB for full identification.")
            self.search_btn.setEnabled(False)
        else:
            self.status.setText("No authorized ADB or Fastboot device found.")
            self.log.append("Check USB cable, drivers, USB debugging authorization, and platform-tools.")
            self.search_btn.setEnabled(False)

    def search(self):
        if not self.device:
            return
        self.search_btn.setEnabled(False)
        self.log.append("\nSearching the official TWRP device directory…")
        self.worker = SearchThread(self.device)
        self.worker.done.connect(self.search_done)
        self.worker.start()

    def search_done(self, results, error):
        self.search_btn.setEnabled(True)
        if error:
            self.log.append(f"Search failed: {error}")
            return
        if not results:
            self.log.append("No likely match found in the official TWRP directory. This does not prove that no community build exists.")
            return
        self.log.append("\nOFFICIAL TWRP DIRECTORY MATCHES (verify codename and instructions):")
        for item in results:
            self.log.append(f"• {item['name']} — {item['url']}")
        self.log.append("\nNo image was downloaded or flashed. Open a result and verify exact device compatibility.")

