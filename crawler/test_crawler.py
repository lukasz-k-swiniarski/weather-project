from crawler_service import CrawlerService
from download_service import DownloadService
from schema_loader import SchemaLoader
from zip_extractor import ZipExtractor
from parser import Parser
from column_mapping import load_column_mapping

if __name__ == "__main__":

    encoding = "cp1250"

    DATASET_CONFIG = {
        "dataset_1": {
            "prefix": "s_d_",
            "encoding": encoding,
            "schema": {
                "source": "url",
                "path": "https://danepubliczne.imgw.pl/data/dane_pomiarowo_obserwacyjne/dane_meteorologiczne/dobowe/synop/s_d_nag%c5%82%c3%b3wek.csv",
                "encoding": encoding,
                "col_mapp": "https://danepubliczne.imgw.pl/data/dane_pomiarowo_obserwacyjne/dane_meteorologiczne/dobowe/synop/s_d_format.txt"
            }
        },
        "dataset_2": {
            "prefix": "s_d_t_",
            "encoding": encoding,
            "schema": {
                "source": "url",
                "path": "https://danepubliczne.imgw.pl/data/dane_pomiarowo_obserwacyjne/dane_meteorologiczne/dobowe/synop/s_d_t_nag%c5%82%c3%b3wek.csv",
                "encoding": encoding,
                "col_mapp": "https://danepubliczne.imgw.pl/data/dane_pomiarowo_obserwacyjne/dane_meteorologiczne/dobowe/synop/s_d_t_format.txt"
            }
        }
    }

    sorted_dataset_dict = dict(
        sorted(
            DATASET_CONFIG.items(),
            key=lambda x: len(x[1]["prefix"]),
            reverse=True
        )
    )

    url = "https://danepubliczne.imgw.pl/data/dane_pomiarowo_obserwacyjne/dane_meteorologiczne/dobowe/synop/"



    crawler = CrawlerService(url)
    downloader = DownloadService()
    extractor = ZipExtractor()
    schema_loader = SchemaLoader()
    parser = Parser(sorted_dataset_dict, schema_loader)

    all_files = []
    files_dic = crawler.crawl()
    for dic in files_dic.values():
        for file in dic.files:
            zip_file_path = downloader.download(file.url)
            files = extractor.extract(zip_file_path)
            all_files.extend(files)

    dataframes = parser.parse(all_files)

    for key, df in dataframes.items():
        col_mapp_url = sorted_dataset_dict[key]["schema"]["col_mapp"]
        col_mapp = load_column_mapping(col_mapp_url)
        dataframes[key] = df.rename(columns=col_mapp)
        print(dataframes[key])


