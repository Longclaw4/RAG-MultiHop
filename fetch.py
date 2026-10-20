import os
import time
import requests

titles = [
    "OpenAI", "Sam Altman", "Microsoft", "Satya Nadella",
    "Google", "Sundar Pichai", "Larry Page", "DeepMind",
    "Demis Hassabis", "YouTube", "Anthropic", "Dario Amodei",
    "Meta Platforms", "Mark Zuckerberg", "Instagram", "WhatsApp",
]

os.makedirs("docs", exist_ok=True)

for title in titles:
    path = "docs/" + title + ".txt"

    if os.path.exists(path):
        print(title, "already downloaded, skipping")
        continue

    r = requests.get(
        "https://en.wikipedia.org/w/api.php",
        params={
            "action": "query",
            "prop": "extracts",
            "explaintext": 1,
            "exintro": 1,
            "redirects": 1,
            "titles": title,
            "format": "json",
        },
        headers={"User-Agent": "graphrag-learning/1.0 (student project)"},
    )

    if r.status_code != 200:
        print(title, "FAILED, status", r.status_code)
        time.sleep(5)
        continue

    try:
        pages = r.json()["query"]["pages"]
    except Exception:
        print(title, "FAILED, bad response")
        time.sleep(5)
        continue

    text = list(pages.values())[0].get("extract", "")

    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

    print(title, len(text))
    time.sleep(4)