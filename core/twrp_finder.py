import requests
from bs4 import BeautifulSoup

INDEX = "https://twrp.me/Devices/"

def find_official_pages(device):
    """Search the official TWRP device index; never selects or flashes a random image."""
    terms = []
    for key in ("codename", "model", "manufacturer"):
        value = (device.get(key) or "").strip().lower()
        if value and value != "unknown":
            terms.append(value)
    if not terms:
        return []
    response = requests.get(INDEX, timeout=20, headers={"User-Agent": "TWRP-Auto-Installer/0.1"})
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    results, seen = [], set()
    for link in soup.select("a[href]"):
        href = link.get("href", "")
        label = " ".join(link.get_text(" ", strip=True).split())
        if not href.startswith("/") or "/Devices/" not in href:
            continue
        haystack = (label + " " + href).lower()
        score = sum(3 if term == (device.get("codename") or "").lower() else 1
                    for term in terms if term in haystack)
        if score and href not in seen:
            seen.add(href)
            url = requests.compat.urljoin(INDEX, href)
            results.append({"name": label or href.rsplit("/", 1)[-1], "url": url, "score": score})
    return sorted(results, key=lambda x: x["score"], reverse=True)[:12]
