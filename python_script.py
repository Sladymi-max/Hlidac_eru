import json
import os
import requests
from bs4 import BeautifulSoup

URL = "https://eru.gov.cz/cenove-vymery"
STATE_FILE = "seen.json"
WEBHOOK_URL = os.getenv("NOTIFY_WEBHOOK_URL")  # např. Slack, Teams nebo Discord


def fetch_decisions() -> dict[str, str]:
    resp = requests.get(URL, timeout=20, headers={"User-Agent": "ERU-Monitor/1.0"})
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    items = {}
    for a in soup.find_all("a", href=True):
        text = " ".join(a.get_text().split())
        if "Cenový výměr" in text:
            href = a["href"]
            full_url = href if href.startswith("http") else f"https://eru.gov.cz{href}"
            items[full_url] = text
    return items


def load_seen() -> set[str]:
    if not os.path.exists(STATE_FILE):
        return set()
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return set(json.load(f))


def save_seen(urls: set[str]) -> None:
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(urls), f, ensure_ascii=False, indent=2)


def notify(new_items: list[tuple[str, str]]) -> None:
    lines = ["Nové cenové výměry na ERÚ:"] + [f"- {title}: {url}" for url, title in new_items]
    message = "\n".join(lines)
    print(message)
    if WEBHOOK_URL:
        requests.post(WEBHOOK_URL, json={"text": message}, timeout=15).raise_for_status()


def main() -> None:
    current = fetch_decisions()
    seen = load_seen()

    # Při prvním běhu jen uloží aktuální stav, aby neposlal historii
    if not seen:
        save_seen(set(current.keys()))
        print(f"Inicializováno {len(current)} položek.")
        return

    new_items = [(url, title) for url, title in current.items() if url not in seen]
    if new_items:
        notify(new_items)
        save_seen(seen | set(current.keys()))
    else:
        print("Žádné nové cenové výměry.")


if __name__ == "__main__":
    main()
