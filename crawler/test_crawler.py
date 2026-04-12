from crawler_service import CrawlerService

if __name__ == "__main__":

    url = "https://danepubliczne.imgw.pl/data/dane_pomiarowo_obserwacyjne/dane_meteorologiczne/dobowe/synop/"

    crawler = CrawlerService(url)

    files_dic = crawler.crawl()

    for dic in files_dic.values():
        for file in dic.files:
            print(file)