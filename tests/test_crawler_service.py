from etl_process.crawler_service import CrawlerService


def test_crawler_restricts_recursion_to_configured_origin_and_path():
    crawler = CrawlerService("https://example.test/data/synop/")

    assert crawler._is_within_base("https://example.test/data/synop/2026/")
    assert not crawler._is_within_base("https://example.test/data/other/")
    assert not crawler._is_within_base("https://other.test/data/synop/")
