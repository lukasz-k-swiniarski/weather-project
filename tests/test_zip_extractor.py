import zipfile

import pytest

from etl_process.zip_extractor import ZipExtractor


def test_extract_rejects_path_traversal(tmp_path):
    archive = tmp_path / "unsafe.zip"
    with zipfile.ZipFile(archive, "w") as zip_file:
        zip_file.writestr("../../outside.txt", "unsafe")

    extractor = ZipExtractor(str(tmp_path / "extracted"))

    with pytest.raises(ValueError, match="Unsafe path"):
        extractor.extract(str(archive))

    assert not (tmp_path / "outside.txt").exists()


def test_extract_replaces_an_incomplete_cache_atomically(tmp_path):
    archive = tmp_path / "weather.zip"
    with zipfile.ZipFile(archive, "w") as zip_file:
        zip_file.writestr("weather.csv", "complete")

    incomplete = tmp_path / "extracted" / "weather"
    incomplete.mkdir(parents=True)
    (incomplete / "stale.csv").write_text("partial", encoding="utf-8")

    extractor = ZipExtractor(str(tmp_path / "extracted"))
    files = extractor.extract(str(archive))

    assert files == [str(incomplete / "weather.csv")]
    assert not (incomplete / "stale.csv").exists()
    assert (incomplete / extractor.COMPLETION_MARKER).is_file()
    assert not (tmp_path / "extracted" / "weather.extracting").exists()
