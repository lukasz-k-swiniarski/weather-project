from crawler.crawler_service import CrawlerService

if __name__ == "__main__":

    url = "YOUR_PAGE_URL"

    crawler = CrawlerService(url)

    files = crawler.crawl()

    for f in files:
        print(f.url, f.filename)