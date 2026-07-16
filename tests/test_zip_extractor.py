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
