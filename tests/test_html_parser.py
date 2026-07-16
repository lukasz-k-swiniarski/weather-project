from etl_process.html_parser import extract_links


def test_extract_links_returns_zip_files_and_subdirectories():
    html = '<a href="sample.zip">data</a><a href="2024/">year</a><a href="../">up</a>'

    directory, subdirectories = extract_links(html, "https://example.com/data/")

    assert [item.filename for item in directory.files] == ["sample.zip"]
    assert subdirectories == ["https://example.com/data/2024/"]
