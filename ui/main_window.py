import webbrowser
from pathlib import Path
from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QFrame, QMessageBox, QInputDialog
)
from core.adb import read_device, read_fastboot
from core.twrp_finder import find_official_pages
from core.compatibility import verify_device_page
from core.unlock import assess_unlock
from core.recovery import get_official_images, download_image

class ScanThread(QThread):
    done = Signal(object, object)
    def run(self):
        self.done.emit(read_device(), read_fastboot())

class SearchThread(QThread):
    done = Signal(object, object)
    def __init__(self, device):
        super().__init__()
        self.device = device
    def run(self):
        try:
            pages = find_official_pages(self.device)
            checked = []
            for page in pages:
                try:
                    verification = verify_device_page(self.device, page)
                except Exception as exc:
                    verification = {"status": "error", "exact": False, "reason": str(exc)}
                checked.append({**page, "verification": verification})
            self.done.emit(checked, None)
        except Exception as exc:
            self.done.emit([], str(exc))

class DownloadThread(QThread):
    done = Signal(object, object)
    def __init__(self, image_url):
        super().__init__()
        self.image_url = image_url
    def run(self):
        try:
            result = download_image(self.image_url, Path.home() / "Downloads" / "TWRP-Auto-Installer")
            self.done.emit(result, None)
        except Exception as exc:
            self.done.emit(None, str(exc))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TWRP Auto Installer")
        self.resize(980, 720)
        self.device = None
        self.pages = []
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        title = QLabel("TWRP AUTO INSTALLER")
        title.setStyleSheet("font-size:25px;font-weight:800;color:#e8edf7")
        subtitle = QLabel("Device diagnostics • OEM unlock guidance • Exact TWRP page checks • Recovery download")
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
        self.search_btn = QPushButton("Find & verify official TWRP")
        self.search_btn.setEnabled(False)
        self.search_btn.clicked.connect(self.search)
        self.download_btn = QPushButton("Download recovery from matched page")
        self.download_btn.setEnabled(False)
        self.download_btn.clicked.connect(self.download)
        row.addWidget(self.scan_btn)
        row.addWidget(self.search_btn)
        row.addWidget(self.download_btn)
        p.addLayout(row)
        layout.addWidget(panel)
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setPlaceholderText("Device details, unlock diagnostics and TWRP verification results appear here…")
        layout.addWidget(self.log, 1)
        warning = QLabel(
            "Safety: unlock eligibility is manufacturer-controlled and cannot be reliably queried universally. "
            "Unlocking may erase all data. This version does NOT unlock the bootloader or flash recovery. "
            "A wrong recovery image or partition can make a device unbootable."
        )
        warning.setWordWrap(True)
        warning.setStyleSheet("color:#e7bd75;padding:8px")
        layout.addWidget(warning)
        self.setStyleSheet("""
            QMainWindow{background:#111824}
            QLabel{color:#e7edf7}
            QPushButton{background:#3867d6;color:white;border:0;border-radius:8px;padding:11px 14px;font-weight:600}
            QPushButton:disabled{background:#465064;color:#aab2bf}
            QTextEdit{background:#172130;color:#dbe5f3;border:1px solid #344256;border-radius:10px;padding:10px}
        """)

    def scan(self):
        self.scan_btn.setEnabled(False)
        self.search_btn.setEnabled(False)
        self.download_btn.setEnabled(False)
        self.status.setText("Scanning ADB and Fastboot…")
        self.log.clear()
        self.worker = ScanThread()
        self.worker.done.connect(self.scan_done)
        self.worker.start()

    def scan_done(self, device, fastboot):
        self.scan_btn.setEnabled(True)
        self.device = device
        self.pages = []
        if device:
            self.status.setText(f"Detected: {device.get('manufacturer')} {device.get('model')} • ADB")
            self.log.append("DEVICE INFORMATION")
            for key in ("manufacturer", "model", "codename", "android", "build", "serial", "oem_unlock_supported"):
                self.log.append(f"{key.replace('_', ' ').title()}: {device.get(key, 'Unknown')}")
            unlock = assess_unlock(device, fastboot)
            self.log.append("\nBOOTLOADER / OEM DIAGNOSTICS")
            self.log.append(f"Result: {unlock['device_signal']}")
            self.log.append(f"Manufacturer: {unlock['manufacturer_profile']['name']}")
            self.log.append(f"Guidance: {unlock['manufacturer_profile']['note']}")
            if unlock["manufacturer_profile"]["url"]:
                self.log.append(f"Official manufacturer site: {unlock['manufacturer_profile']['url']}")
            self.log.append(unlock["warning"])
            self.search_btn.setEnabled(True)
        elif fastboot:
            self.status.setText(f"Detected Fastboot device • {fastboot['bootloader']}")
            self.log.append(f"Fastboot serial: {fastboot['serial']}")
            self.log.append(f"Bootloader: {fastboot['bootloader']}")
            self.log.append("\nFastboot mode may not expose model/codename. Reboot to Android and scan via ADB for full identification.")
        else:
            self.status.setText("No authorized ADB or Fastboot device found.")
            self.log.append("Check USB cable, drivers, USB debugging authorization, and platform-tools.")

    def search(self):
        if not self.device:
            return
        self.search_btn.setEnabled(False)
        self.download_btn.setEnabled(False)
        self.log.append("\nSearching official TWRP device directory and checking each candidate page…")
        self.worker = SearchThread(self.device)
        self.worker.done.connect(self.search_done)
        self.worker.start()

    def search_done(self, results, error):
        self.search_btn.setEnabled(True)
        if error:
            self.log.append(f"Search failed: {error}")
            return
        self.pages = results
        exact = [x for x in results if x.get("verification", {}).get("exact")]
        if not results:
            self.log.append("No candidate found in the official TWRP directory. Community builds are not checked.")
            return
        self.log.append("\nTWRP DIRECTORY RESULTS")
        for item in results:
            check = item.get("verification", {})
            self.log.append(f"• {item['name']} — {item['url']}")
            self.log.append(f"  Check: {check.get('status', 'unknown')} — {check.get('reason', '')}")
        if exact:
            self.download_btn.setEnabled(True)
            self.log.append("\nAt least one candidate passed the page text check (codename + model). Still compare the exact hardware variant and official installation instructions.")
        else:
            self.log.append("\nNo result passed the strict codename + model check. Recovery download is disabled.")
        self.log.append("This check is a useful filter, not a guarantee of compatibility.")

    def download(self):
        exact = [x for x in self.pages if x.get("verification", {}).get("exact")]
        if not exact:
            QMessageBox.warning(self, "Not verified", "No exact directory-page text match is available.")
            return
        page, ok = QInputDialog.getItem(self, "Choose device page", "Official TWRP page with matching model/codename text:", [x["name"] for x in exact], 0, False)
        if not ok:
            return
        selected = next(x for x in exact if x["name"] == page)
        try:
            images = get_official_images(selected["url"])
        except Exception as exc:
            QMessageBox.critical(self, "Could not read downloads", str(exc))
            return
        if not images:
            QMessageBox.information(self, "No image links", "No .img download link was found on this official page.")
            return
        labels = [f'{x["name"]} ({x["url"]})' for x in images]
        chosen, ok = QInputDialog.getItem(self, "Choose recovery image", "Image linked by the official device page:", labels, 0, False)
        if not ok:
            return
        image = images[labels.index(chosen)]
        confirm = QMessageBox.warning(
            self, "Confirm download",
            "Download this image only? This does not verify that it is suitable for your exact hardware revision, and it will NOT be flashed.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        self.download_btn.setEnabled(False)
        self.log.append(f"\nDownloading {image['name']}…")
        self.worker = DownloadThread(image["url"])
        self.worker.done.connect(self.download_done)
        self.worker.start()

    def download_done(self, result, error):
        self.download_btn.setEnabled(True)
        if error:
            self.log.append(f"Download failed: {error}")
            QMessageBox.critical(self, "Download failed", error)
            return
        self.log.append("\nDOWNLOAD COMPLETE")
        self.log.append(f"File: {result['path']}")
        self.log.append(f"Size: {result['size']} bytes")
        self.log.append(f"SHA-256: {result['sha256']}")
        self.log.append("Checksum status: NOT publisher-verified; only a local hash was calculated.")
        QMessageBox.information(self, "Download complete", f"Saved to:\n{result['path']}\n\nSHA-256:\n{result['sha256']}")

