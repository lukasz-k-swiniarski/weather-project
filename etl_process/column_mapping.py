import unicodedata

import requests


def remove_diacritics(text: str) -> str:
    normalized = unicodedata.normalize('NFKD', text)
    return ''.join(c for c in normalized if not unicodedata.combining(c))


def load_column_mapping(url: str) -> dict:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    text = response.text

    mapping = {}
    for line in text.splitlines():
        line = remove_diacritics(line)  # 👈 this is the key part

        parts = line.strip().split(maxsplit=1)
        if len(parts) == 2:
            key, value = parts
            mapping[key] = value

    return mapping
