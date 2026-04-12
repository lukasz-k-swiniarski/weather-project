from models import FileLink, FileLinkDirectory
from bs4 import BeautifulSoup
from urllib.parse import urljoin


def extract_links(html: str, base_url: str):
    soup = BeautifulSoup(html, "html.parser")

    zip_links: list[FileLink] = []
    directory_links = []

    for a in soup.find_all("a", href=True):
        href = a["href"]
        full_url = urljoin(base_url, href)

        if href.endswith(".zip"):
            zip_links.append(
                FileLink(
                    url=full_url,
                    filename=href.split("/")[-1],
                    source_page=base_url
                )
            )

        elif href.endswith("/") and not href.startswith("../") and not len(full_url) < len(base_url):
            directory_links.append(full_url)

    return FileLinkDirectory(files=zip_links,directory_url=base_url, directory=base_url.split("/")[-2]), directory_links