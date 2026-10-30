"""Conservative recovery image download helpers; no flashing is performed here."""
import hashlib
import os
from pathlib import Path
from urllib.parse import urlparse, urljoin

import requests
from bs4 import BeautifulSoup

OFFICIAL_HOSTS = {"twrp.me", "www.twrp.me"}

def get_official_images(device_page_url):
    parsed = urlparse(device_page_url)
    if parsed.scheme != "https" or parsed.hostname not in OFFICIAL_HOSTS or not parsed.path.startswith("/Devices/"):
        raise ValueError("Only device pages on the official HTTPS twrp.me site are accepted.")
    response = requests.get(device_page_url, timeout=25, headers={"User-Agent": "TWRP-Auto-Installer/0.2"})
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    found, seen = [], set()
    for a in soup.select("a[href]"):
        href = urljoin(device_page_url, a["href"])
        p = urlparse(href)
        if p.scheme != "https" or not p.path.lower().endswith(".img"):
            continue
        if href in seen:
            continue
        seen.add(href)
        found.append({"name": a.get_text(" ", strip=True) or Path(p.path).name, "url": href})
    return found

def download_image(image_url, output_dir):
    parsed = urlparse(image_url)
    if parsed.scheme != "https" or not parsed.path.lower().endswith(".img"):
        raise ValueError("Only HTTPS .img files are accepted.")
    # The image URL must have been obtained from an official TWRP device page by get_official_images.
    response = requests.get(image_url, timeout=90, stream=True, headers={"User-Agent": "TWRP-Auto-Installer/0.2"})
    response.raise_for_status()
    name = Path(parsed.path).name or "recovery.img"
    folder = Path(output_dir)
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / name
    digest = hashlib.sha256()
    size = 0
    with target.open("wb") as f:
        for chunk in response.iter_content(1024 * 256):
            if not chunk:
                continue
            size += len(chunk)
            if size > 2 * 1024 * 1024 * 1024:
                f.close()
                target.unlink(missing_ok=True)
                raise ValueError("Image exceeds the 2 GiB safety limit.")
            digest.update(chunk)
            f.write(chunk)
    return {"path": str(target), "size": size, "sha256": digest.hexdigest(),
            "verified": False,
            "message": "SHA-256 calculated locally. It is not verified against a publisher checksum."}
