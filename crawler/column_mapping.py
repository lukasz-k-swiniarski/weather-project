import requests

def load_column_mapping(url: str) -> dict:
    """
    Downloads and parses column mapping from a text file.

    Expected format:
    CODE    Description
    NSP     Kod stacji
    POST    Nazwa stacji
    """

    text = requests.get(url).text

    mapping = {}
    for line in text.splitlines():
        parts = line.strip().split(maxsplit=1)
        if len(parts) == 2:
            key, value = parts
            mapping[key] = value

    return mapping