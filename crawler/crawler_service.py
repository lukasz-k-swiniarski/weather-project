import requests
from crawler.parser import extract_links


class CrawlerService:

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.headers = {"User-Agent": "Mozilla/5.0"}
        self.visited = set()
        self.zip_files_dic = {}
        self.directories = []

    def crawl(self):
        self._crawl_page(self.base_url)
        return self.zip_files_dic

    def _crawl_page(self, url):
        print(url)
        if url in self.visited:
            return

        self.visited.add(url)

        response = requests.get(url, headers=self.headers, timeout=30)
        response.raise_for_status()

        zip_links_dir, directory_links = extract_links(response.text, url)

        if zip_links_dir.files: self.zip_files_dic[zip_links_dir.directory] = zip_links_dir

        for directory in directory_links:
            if directory not in self.visited:
                self._crawl_page(directory)