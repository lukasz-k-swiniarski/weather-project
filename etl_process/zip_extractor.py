import logging
import os
import zipfile
from pathlib import Path

logger = logging.getLogger(__name__)


class ZipExtractor:
    def __init__(self, extract_dir: str = "data/extracted"):
        self.extract_dir = extract_dir
        os.makedirs(self.extract_dir, exist_ok=True)

    def _get_extract_path(self, zip_path: str) -> str:
        zip_name = os.path.splitext(os.path.basename(zip_path))[0]
        return os.path.join(self.extract_dir, zip_name)

    def extract(self, zip_path: str) -> list[str]:
        extract_path = self._get_extract_path(zip_path)

        # idempotency – jeśli już rozpakowane
        if os.path.exists(extract_path) and os.listdir(extract_path):
            logger.info(f"Already extracted, skipping: {extract_path}")
            return self._list_files(extract_path)

        try:
            logger.info(f"Extracting {zip_path} → {extract_path}")

            os.makedirs(extract_path, exist_ok=True)

            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                self._validate_members(zip_ref, extract_path)
                zip_ref.extractall(extract_path)

            files = self._list_files(extract_path)

            logger.info(f"Extracted {len(files)} files")
            return files

        except zipfile.BadZipFile:
            logger.error(f"Invalid ZIP file: {zip_path}")
            raise

        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            raise

    @staticmethod
    def _validate_members(zip_ref: zipfile.ZipFile, extract_path: str) -> None:
        target_dir = Path(extract_path).resolve()

        for member in zip_ref.infolist():
            member_path = (target_dir / member.filename).resolve()
            if target_dir != member_path and target_dir not in member_path.parents:
                raise ValueError(f"Unsafe path in ZIP archive: {member.filename}")

    def _list_files(self, directory: str) -> list[str]:
        file_paths = []

        for root, _, files in os.walk(directory):
            for file in files:
                file_paths.append(os.path.join(root, file))

        return file_paths
