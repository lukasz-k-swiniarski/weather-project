import io
import zipfile
from unittest.mock import MagicMock, patch

import pytest

from etl_process.download_service import DownloadService


def zip_bytes(filename: str = "weather.csv", content: str = "data") -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(filename, content)
    return buffer.getvalue()


def response_with(content: bytes) -> MagicMock:
    response = MagicMock()
    response.__enter__.return_value = response
    response.iter_content.return_value = [content]
    return response


def test_download_publishes_only_a_valid_complete_archive(tmp_path):
    service = DownloadService(str(tmp_path), retries=1)
    response = response_with(zip_bytes())

    with patch("etl_process.download_service.requests.get", return_value=response):
        path = service.download("https://example.test/weather.zip")

    assert zipfile.is_zipfile(path)
    assert not (tmp_path / "weather.zip.part").exists()


def test_download_replaces_an_invalid_cached_archive(tmp_path):
    cached = tmp_path / "weather.zip"
    cached.write_bytes(b"partial")
    service = DownloadService(str(tmp_path), retries=1)

    with patch(
        "etl_process.download_service.requests.get",
        return_value=response_with(zip_bytes()),
    ):
        path = service.download("https://example.test/weather.zip")

    assert path == str(cached)
    assert zipfile.is_zipfile(cached)


def test_download_failure_leaves_no_partial_or_published_file(tmp_path):
    service = DownloadService(str(tmp_path), retries=1)

    with patch(
        "etl_process.download_service.requests.get",
        return_value=response_with(b"not a zip"),
    ):
        with pytest.raises(RuntimeError, match="valid archive"):
            service.download("https://example.test/weather.zip")

    assert not (tmp_path / "weather.zip").exists()
    assert not (tmp_path / "weather.zip.part").exists()
