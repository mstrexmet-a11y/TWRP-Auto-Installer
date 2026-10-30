"""Exact-device checks for official TWRP directory entries."""
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

def normalize(value):
    return re.sub(r"[^a-z0-9]+", "", (value or "").lower())

def verify_device_page(device, page):
    url = page.get("url", "")
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in ("twrp.me", "www.twrp.me") or not parsed.path.startswith("/Devices/"):
        return {"status": "rejected", "reason": "Not an official TWRP device page.", "exact": False}
    response = requests.get(url, timeout=25, headers={"User-Agent": "TWRP-Auto-Installer/0.2"})
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    text = " ".join(soup.stripped_strings)
    codename = normalize(device.get("codename"))
    model = normalize(device.get("model"))
    page_text = normalize(text + " " + url)
    code_match = bool(codename and len(codename) >= 3 and codename in page_text)
    model_match = bool(model and len(model) >= 4 and model in page_text)
    if code_match and model_match:
        return {"status": "exact-directory-match", "exact": True,
                "reason": "Codename and model both appear on the official device page.",
                "title": soup.title.get_text(" ", strip=True) if soup.title else url}
    if code_match:
        return {"status": "codename-match-only", "exact": False,
                "reason": "Codename appears, but model could not also be confirmed. Manual variant check required."}
    return {"status": "not-verified", "exact": False,
            "reason": "The page does not confirm this device's codename. Do not download or flash from this match."}
