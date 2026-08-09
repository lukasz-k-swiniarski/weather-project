import logging
import os
import zipfile
from pathlib import Path
from urllib.parse import urlparse

import requests

logger = logging.getLogger(__name__)


class DownloadService:
    def __init__(
        self,
        download_dir: str = "data/raw",
        retries: int = 3,
        timeout: int = 10,
    ):
        self.download_dir = Path(download_dir)
        self.retries = retries
        self.timeout = timeout
        self.download_dir.mkdir(parents=True, exist_ok=True)

    def _get_filename_from_url(self, url: str) -> str:
        filename = os.path.basename(urlparse(url).path)
        if not filename:
            raise ValueError(f"Download URL has no filename: {url}")
        return filename

    @staticmethod
    def _validate_zip(path: Path) -> None:
        if not zipfile.is_zipfile(path):
            raise zipfile.BadZipFile(f"Invalid ZIP archive: {path}")
        with zipfile.ZipFile(path) as archive:
            invalid_member = archive.testzip()
        if invalid_member is not None:
            raise zipfile.BadZipFile(
                f"Corrupt ZIP member {invalid_member!r} in {path}"
            )

    def download(self, url: str) -> str:
        file_path = self.download_dir / self._get_filename_from_url(url)
        temporary_path = file_path.with_suffix(f"{file_path.suffix}.part")

        if file_path.exists():
            try:
                self._validate_zip(file_path)
            except zipfile.BadZipFile:
                logger.warning("Cached archive is invalid and will be replaced: %s", file_path)
            else:
                logger.info("Validated cached archive: %s", file_path)
                return str(file_path)

        for attempt in range(1, self.retries + 1):
            try:
                logger.info("Downloading %s (attempt %s)", url, attempt)
                with requests.get(
                    url,
                    timeout=self.timeout,
                    stream=True,
                ) as response:
                    response.raise_for_status()
                    with temporary_path.open("wb") as destination:
                        for chunk in response.iter_content(chunk_size=1024 * 1024):
                            if chunk:
                                destination.write(chunk)

                self._validate_zip(temporary_path)
                os.replace(temporary_path, file_path)
                logger.info("Downloaded and validated: %s", file_path)
                return str(file_path)
            except (requests.RequestException, OSError, zipfile.BadZipFile) as exc:
                temporary_path.unlink(missing_ok=True)
                logger.warning("Download attempt %s failed: %s", attempt, exc)
                if attempt == self.retries:
                    raise RuntimeError(
                        f"Failed to download a valid archive after {self.retries} "
                        f"attempts: {url}"
                    ) from exc

        raise RuntimeError(f"Download attempts exhausted unexpectedly: {url}")
