from urllib.parse import urlparse

import requests

from etl_process.html_parser import extract_links


class CrawlerService:

    def __init__(self, base_url: str):
        self.base_url = base_url
        parsed_base = urlparse(base_url)
        self.base_origin = (parsed_base.scheme, parsed_base.netloc)
        self.base_path = parsed_base.path.rstrip("/") + "/"
        self.headers = {"User-Agent": "Mozilla/5.0"}
        self.visited = set()
        self.zip_files_dic = {}
        self.directories = []

    def crawl(self):
        self._crawl_page(self.base_url)
        return self.zip_files_dic

    def _crawl_page(self, url):
        if not self._is_within_base(url):
            return

        if url in self.visited:
            return

        self.visited.add(url)

        response = requests.get(url, headers=self.headers, timeout=30)
        response.raise_for_status()

        zip_links_dir, directory_links = extract_links(response.text, url)

        if zip_links_dir.files:
            self.zip_files_dic[zip_links_dir.directory] = zip_links_dir

        for directory in directory_links:
            if directory not in self.visited:
                self._crawl_page(directory)

    def _is_within_base(self, url: str) -> bool:
        parsed = urlparse(url)
        return (
            (parsed.scheme, parsed.netloc) == self.base_origin
            and (parsed.path.rstrip("/") + "/").startswith(self.base_path)
        )
