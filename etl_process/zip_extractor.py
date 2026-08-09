import logging
import os
import shutil
import zipfile
from pathlib import Path

logger = logging.getLogger(__name__)


class ZipExtractor:
    COMPLETION_MARKER = ".extraction-complete"

    def __init__(self, extract_dir: str = "data/extracted"):
        self.extract_dir = Path(extract_dir)
        self.extract_dir.mkdir(parents=True, exist_ok=True)

    def _get_extract_path(self, zip_path: str) -> Path:
        return self.extract_dir / Path(zip_path).stem

    def extract(self, zip_path: str) -> list[str]:
        extract_path = self._get_extract_path(zip_path)
        marker = extract_path / self.COMPLETION_MARKER

        if marker.is_file():
            files = self._list_files(extract_path)
            if files:
                logger.info("Validated extracted archive cache: %s", extract_path)
                return files

        temporary_path = extract_path.with_name(f"{extract_path.name}.extracting")
        if temporary_path.exists():
            shutil.rmtree(temporary_path)
        temporary_path.mkdir(parents=True)

        try:
            logger.info("Extracting %s -> %s", zip_path, extract_path)
            with zipfile.ZipFile(zip_path, "r") as archive:
                self._validate_members(archive, temporary_path)
                invalid_member = archive.testzip()
                if invalid_member is not None:
                    raise zipfile.BadZipFile(
                        f"Corrupt ZIP member {invalid_member!r} in {zip_path}"
                    )
                archive.extractall(temporary_path)

            files = self._list_files(temporary_path)
            if not files:
                raise ValueError(f"ZIP archive contains no files: {zip_path}")

            (temporary_path / self.COMPLETION_MARKER).write_text(
                "complete\n",
                encoding="utf-8",
            )
            if extract_path.exists():
                shutil.rmtree(extract_path)
            os.replace(temporary_path, extract_path)

            files = self._list_files(extract_path)
            logger.info("Extracted %s files", len(files))
            return files
        except Exception:
            shutil.rmtree(temporary_path, ignore_errors=True)
            logger.exception("Extraction failed for %s", zip_path)
            raise

    @staticmethod
    def _validate_members(archive: zipfile.ZipFile, extract_path: Path) -> None:
        target_dir = extract_path.resolve()
        for member in archive.infolist():
            member_path = (target_dir / member.filename).resolve()
            if target_dir != member_path and target_dir not in member_path.parents:
                raise ValueError(f"Unsafe path in ZIP archive: {member.filename}")

    def _list_files(self, directory: Path) -> list[str]:
        return sorted(
            str(path)
            for path in directory.rglob("*")
            if path.is_file() and path.name != self.COMPLETION_MARKER
        )
