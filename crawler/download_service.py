import os
import requests
import logging
from urllib.parse import urlparse

logging.basicConfig(level=logging.INFO)


class DownloadService:
    def __init__(self, download_dir: str = "data/raw", retries: int = 3, timeout: int = 10):
        self.download_dir = download_dir
        self.retries = retries
        self.timeout = timeout

        os.makedirs(self.download_dir, exist_ok=True)

    def _get_filename_from_url(self, url: str) -> str:
        parsed = urlparse(url)
        return os.path.basename(parsed.path)

    def download(self, url: str) -> str:
        filename = self._get_filename_from_url(url)
        file_path = os.path.join(self.download_dir, filename)

        # idempotency – nie pobieraj drugi raz
        if os.path.exists(file_path):
            logging.info(f"File already exists, skipping: {file_path}")
            return file_path

        for attempt in range(1, self.retries + 1):
            try:
                logging.info(f"Downloading {url} (attempt {attempt})")

                response = requests.get(url, timeout=self.timeout)
                response.raise_for_status()

                with open(file_path, "wb") as f:
                    f.write(response.content)

                logging.info(f"Downloaded: {file_path}")
                return file_path

            except requests.RequestException as e:
                logging.warning(f"Attempt {attempt} failed: {e}")

                if attempt == self.retries:
                    logging.error(f"Failed to download after {self.retries} attempts: {url}")
                    raise

        return None