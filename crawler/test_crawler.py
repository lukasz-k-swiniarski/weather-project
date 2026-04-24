from crawler_service import CrawlerService
from download_service import DownloadService
from schema_loader import SchemaLoader
from zip_extractor import ZipExtractor
from parser import Parser
from column_mapping import load_column_mapping
from postgres_client import PostgresClient
from config import get_db_config, get_dataset_config, get_dataset_schema_config

if __name__ == "__main__":

    db_config = get_db_config()
    db = PostgresClient(**db_config)
    db.connect()

    dataset_config = get_dataset_config()
    dataset_schema_config = get_dataset_schema_config()

    sorted_dataset_dict = dict(
        sorted(
            dataset_schema_config.items(),
            key=lambda x: len(x[1]["prefix"]),
            reverse=True
        )
    )

    crawler = CrawlerService(dataset_config['url'])
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
            #break
        #break

    dataframes = parser.parse(all_files)

    for key, df in dataframes.items():
        col_mapp_url = sorted_dataset_dict[key]["schema"]["col_mapp"]
        db.upload_dataframe(dataframes[key],f'Synop data {key}')
        #col_mapp = load_column_mapping(col_mapp_url)
        #dataframes[key] = df.rename(columns=col_mapp)
        print(dataframes[key])



